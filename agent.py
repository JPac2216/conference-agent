import os
import extract_schedule, add_csv_to_chroma
import streamlit as st

path = "apha2025_sessions.csv"

# Extract the APHA 2025 session schedule
if not os.path.exists(path):
    extract_schedule.main()
else:
    print(f"'{path}' already exists. Skipping extraction.")

#Creating the ChromaDB
add_csv_to_chroma.populate_from_csv(path)

#Import LLM and LangGraph structure
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage
from operator import add as add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool

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
    
tools = [retriever_tool]
tools_dict = {our_tool.name: our_tool for our_tool in tools}

# Allow the LLM to use the tools
llm = llm.bind_tools(tools)

# Keeping track of information
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
system_prompt = """
You are an intelligent AI assistant who answers questions about public health conferences and is able to help users plan sessions based on the 'apha2025_sessions.csv' file loaded into your knowledge base.
Use the retriever tool available to answer any questions regarding all networking, happy hours and social events within this program. When you need to search the database, call retriever_tool with 3–5 **keywords** only, not full sentences.

Example: Say the user is asking for conferences about COVID on March 22:

{ "name": "retriever_tool",
  "args": { "query": "COVID-19, 2025-03-22, vaccine updates, real-world data" }
}

Please provide dates, times (in standard time NOT military time) and locations. Please include special interest groups.
You can make multiple calls if needed. If you need to look up some information before asking a follow up question, you are allowed to do that!
Please always cite exactly where you got your answer.
"""

# LLM Agent
def call_llm(state: AgentState) -> AgentState:
    """Function to call the LLM with the current state"""
    messages = list(state['messages'])

    messages = [SystemMessage(content=system_prompt)] + messages

    message = llm.invoke(messages)
    return {'messages': messages + [message]}

# Retrieval agent
def call_tools(state: AgentState) -> AgentState:
    """Execute tool calls from teh LLM's response."""
    tool_calls = state['messages'][-1].tool_calls
    results = []
    for t in tool_calls:
        print(f"Calling Tool: {t['name']} with query: {t['args'].get('query', 'No query provided')}")

        # Checking tool validity
        if not t['name'] in tools_dict:
            print(f"\nTool: {t['name']} does not exist.")
            result = "Incorrect Tool Name, Please Retry and Select tool from List of Available tools."

        else:
            result = tools_dict[t['name']].invoke(t['args'].get('query', ''))
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
    print("\n=== RAG AGENT===")
    
    state: AgentState = {"messages": []}
    while True:
        user_input = input("\nWhat is your question: ")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        state['messages'].append(HumanMessage(content=user_input))

        result = agent.invoke(state)
        
        print("\n=== ANSWER ===")
        print(result['messages'][-1].content)

running_agent()