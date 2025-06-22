import os
import extract_schedule, add_csv_to_chroma
import streamlit as st

path = "apha2025_sessions.csv"

# # Extract the APHA 2025 session schedule
# if not os.path.exists(path):
#     extract_schedule.main()
# else:
#     print(f"'{path}' already exists. Skipping extraction.")

# #Creating the ChromaDB
# add_csv_to_chroma.populate_from_csv(path)

#Import LLM and LangGraph structure
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage
from operator import add as add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
import requests
import json

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0
)

@tool
def retriever_tool(query: str) -> str:
    """This tool searches the Chroma database containing all of the session info and returns the top 10 chunks."""
    query_embedding = add_csv_to_chroma.embedder.encode([query])[0]
    query_results = add_csv_to_chroma.collection.query(query_embeddings=[query_embedding], n_results=10)
    result = ""
    if query_results and query_results['documents'] and query_results['distances']:
        for i, doc in enumerate(query_results['documents'][0]):
            result += f"""
TEXT: {doc}
SCORE: {query_results['distances'][0][i]}
            """
        return result
    else:
        return "I found no relevant information in the APHA 2025 Session schedule."

@tool    
def linkedin_search_tool(name: str, title: str, institution: str) -> str:
    """This tool retrieves a presenter's LinkedIn profile (if available) given their full name, professional title, and institution.
    Args:
    name: Presenter's full name given by the database query
    title: Presenter's company title given by the database query
    institution: Presenter's institution given by the database query
    """

    url = "https://api.tavily.com/search"

    payload = {
        "query": f"Find {name}'s LinkedIn profile, they are the {title} at {institution}."
    }
    headers = {
        "Authorization": f"Bearer {os.environ['TAVILY_API_KEY']}",
        "Content-Type": "application/json"
    }

    response = requests.request("POST", url, json=payload, headers=headers)

    #print(response.text)
    dict = json.loads(response.text)
    raw_url = dict["results"][0]["url"]

    if "/posts/" in raw_url or "/activity/" in raw_url:
        profile = raw_url.split("linkedin.com/")[1].split("/")[1].split("_")[0]
        return f"https://www.linkedin.com/in/{profile}"
    return raw_url

tools = [retriever_tool, linkedin_search_tool]
tools_dict = {our_tool.name: our_tool for our_tool in tools}

# Allow the LLM to use the tools
llm = llm.bind_tools(tools)

# Keeping track of information
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
system_prompt = """
You are an intelligent AI assistant who answers questions about public health conferences and is able to help users plan sessions based on the 'apha2025_sessions.csv' file loaded into your knowledge base.
Always focus your response **only on the user's most recent message**. Ignore earlier user questions unless explicitly referenced.

Use the retriever tool available to answer the user's latest question regarding all events within the program. When you need to search the database, call retriever_tool with roughly 3–5 **keywords**, not full sentences.

Example: Say the user is asking for conferences about COVID on March 22:

{ "name": "retriever_tool",
  "args": { "query": "COVID-19, 2025-03-22, vaccine updates, real-world data" }
}

Summarize the event for the user with relevent info you find from the tool, and offer assistance based on the user's question. 

Please provide dates, times (in standard time NOT military time) and locations. Please include special interest groups.
Include if the user is able to preregister for the event (based on the TRUE/FALSE) data.

Additionally include the speakers, which may be provided either in the 'Presenters' key or in the description itself. 
For EACH speaker included find their LinkedIn profiles by using the LinkedIn search tool and feed it each presenter's full name, title, and institution based on the info given to you from the retriever tool.

    Example: Say the retriever tool gives you:

    Presenters: Jake Paccione
    Professional Titles: Undergraduate Research Assistant
    Institutions: Stevens Institute of Technology

    Use the LinkedIn Search Tool:

    { "name": "linkedin_search_tool",
    "args": { "name": "Jake Paccione", "title": "Undergraduate Research Assistant", "institution": "Stevens Institute of Technology" }
    }

    If you cannot find a relevant result, inform the user that you could not find their LinkedIn profile.

If you need to look up some information before asking a follow up question, you are allowed to do that!
Please always cite exactly where you got your answer.
"""

# LLM Agent
def call_llm(state: AgentState) -> AgentState:
    """Function to call the LLM with the current state"""
    messages = list(state['messages'])

    model_messages = [SystemMessage(content=system_prompt)] + messages

    message = llm.invoke(model_messages)
    return {'messages': state['messages'] + [message]}

# Retrieval agent
def call_tools(state: AgentState) -> AgentState:
    """Execute tool calls from teh LLM's response."""
    tool_calls = state['messages'][-1].tool_calls
    results = []
    for t in tool_calls:
        print(f"Calling Tool: {t['name']} with query: {t['args']}")

        # Checking tool validity
        if not t['name'] in tools_dict:
            print(f"\nTool: {t['name']} does not exist.")
            result = "Incorrect Tool Name, Please Retry and Select tool from List of Available tools."

        else:
            result = tools_dict[t['name']].invoke(t['args'])
            print(f"Result length: {len(str(result))}")

        results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))

    print("Tools Execution Complete. Back to the model!")
    return {'messages': state['messages'] + results}

# Setting up conditional edge
def llm_path(state: AgentState) -> str:
    """Checks if the last message contains tool calls"""
    result = state['messages'][-1]
    return "True" if (hasattr(result, 'tool_calls') and len(result.tool_calls) > 0) else "False"

graph = StateGraph(AgentState)

graph.add_node("llm", call_llm)
graph.add_node("retriever", call_tools)

graph.add_edge(START, "llm")
graph.add_conditional_edges(
    "llm",
    llm_path,
    {
        "True": "retriever",
        "False": END
    }
)
graph.add_edge("retriever", "llm")

agent = graph.compile()

def running_agent():
    # print("\n=== RAG AGENT===")
    st.title("RAG Conference Planning Agent :material/check_box:")

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    for msg in st.session_state["messages"]:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        with st.chat_message(role):
            if role == "user":
                st.write(msg.content)
            else:
                st.write(msg)

    user_input = st.chat_input("Say something", key="chat_input")
    if user_input:
        with st.chat_message("user"):
            st.write(user_input)

        st.session_state["messages"].append(HumanMessage(content=user_input))

        state: AgentState = {"messages": st.session_state["messages"]}
        result = agent.invoke(state)

        with st.chat_message("assistant"):
            st.write(result["messages"][-1].content)

        st.session_state["messages"].append(result["messages"][-1].content)

running_agent()