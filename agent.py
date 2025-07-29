"""
Notes for 7/10
- Network diagram? (networkx)
- ChromaDB updates
- Error | done
- Fix naccho | done
"""

import os
import extract_apha, extract_naccho, add_csv_to_chroma
import streamlit as st

#Import LLM and LangGraph structure
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage, AIMessage
from operator import add as add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
import requests
import json

# Import Table tools
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.section import WD_ORIENT

# Import Types for expected structures
from typing_extensions import TypedDict, List

class PresenterInfo(TypedDict):
    names: str
    professional_titles: str
    institution: str
    city_state: str
    title: str
    dtl: str
    bio: str

apha_path = "apha2025_sessions.csv"
naccho_path = "naccho2025_sessions.csv"
chiexpo_path = "chiexpo2025_sessions.csv"

chroma_path = "chroma_data/"
table_path = "table.docx"

# Extract the APHA 2025 session schedule
if not os.path.exists(apha_path):
    print("Extracting sessions for APhA 2025...")
    extract_apha.main()
    add_csv_to_chroma.populate_from_csv(apha_path, "APhA 2025")

# Extract the NACCHO 2025 session schedule
if not os.path.exists(naccho_path):
    print("Extracting sessions for NACCHO360 2025...")
    extract_naccho.main()
    add_csv_to_chroma.populate_from_csv(naccho_path, "NACCHO360 2025")

# Extract the CHI & Expo 2025 session schedule
if not os.path.exists(chiexpo_path):
    print("Extracting sessions for CHI Community Health Conference & Expo 2025...")
    extract_naccho.main()
    add_csv_to_chroma.populate_from_csv(chiexpo_path, "CHI Community Health Conference & Expo 2025")

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0
)

# Establish tools for the LLM to use
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

    dict = json.loads(response.text)

    if not dict.get("results") or len(dict["results"]) == 0 or "linkedin" not in dict["results"][0]["url"]:
        return ""

    raw_url = dict["results"][0]["url"]

    if "/posts/" in raw_url or "/activity/" in raw_url:
        profile = raw_url.split("linkedin.com/")[1].split("/")[1].split("_")[0]
        return f"https://www.linkedin.com/in/{profile}"
    return raw_url

# Helper function for table tool
def set_table_border(table):
    tbl = table._tbl
    tblPr = tbl.tblPr

    tblBorders = OxmlElement('w:tblBorders')
    for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
        border = OxmlElement(f'w:{border_name}')
        border.set(qn('w:val'), 'single')
        border.set(qn('w:sz'), '4')
        border.set(qn('w:space'), '0')
        border.set(qn('w:color'), 'auto')
        tblBorders.append(border)

    tblPr.append(tblBorders)

@tool
def table_tool(info: List[PresenterInfo]):
    """This tool uses info from the database to generate a table output in docx that gets returned to the user.
    Args:
        info: List of PresenterInfo dictionaries including:
            names: Names of presenters
            professional titles: Titles for each presenter
            institution: presenter's institution
            city_state: City / State of presenters, try to get as specific as possible
            title: Title of presentation
            dtl: Date, time, and location
            bio: Each presenter's LinkedIn
    """

    document = Document()

    section = document.sections[-1]
    section.orientation = WD_ORIENT.LANDSCAPE

    new_width, new_height = section.page_height, section.page_width
    section.page_width = new_width
    section.page_height = new_height

    table = document.add_table(rows=len(info) + 1, cols=7)
    set_table_border(table)

    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "Name of Presenter (s)"
    hdr_cells[1].text = "Professional Title"
    hdr_cells[2].text = "Institution"
    hdr_cells[3].text = "City / State"
    hdr_cells[4].text = "Title of Presentation"
    hdr_cells[5].text = "Date, time and location"
    hdr_cells[6].text = "Biography"

    for i, dict in enumerate(info):
        row_cells = table.rows[i+1].cells
        row_cells[0].text = dict.get("names")
        row_cells[1].text = dict.get("professional_titles")
        row_cells[2].text = dict.get("institution")
        row_cells[3].text = dict.get("city_state")
        row_cells[4].text = dict.get("title")
        row_cells[5].text = dict.get("dtl")
        row_cells[6].text = dict.get("bio")

    document.save('table.docx')

    return "Table successfully created."

tools = [retriever_tool, linkedin_search_tool, table_tool]
tools_dict = {our_tool.name: our_tool for our_tool in tools}

# Allow the LLM to use the tools
llm = llm.bind_tools(tools)

# Keeping track of information
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
system_prompt = """
You are an intelligent AI assistant that answers questions about public health conferences and helps users plan sessions using data from a ChromaDB-backed knowledge base.

Always respond ONLY to the user's **most recent message**. Ignore prior user inputs unless they are referenced again.

When the user asks about event sessions or people, use the `retriever_tool` to search the database. DO NOT respond based on your own knowledge unless explicitly instructed to.

When the user asks for info in table format, use the `table_tool` to generate a downloadable DOCX document.

Only use the `linkedin_search_tool` if the user EXPLICITLY asks for LinkedIn profiles of presenters OR if you are using the table_tool.

---
### TOOL INSTRUCTIONS

#### TOOL: `retriever_tool`
Use this when the user asks about specific conference sessions, presenters, topics, or events.

**Call Example**:

Question: What sessions on covid are there on March 22?
{
  "name": "retriever_tool",
  "args": {
    "query": "COVID-19, 2025-03-22, vaccine updates, real-world data"
  }
}

**Search Tips**:
- Use ~3-5 keywords, not full sentences
- Include date, topic, or speaker names if relevant

---

#### TOOL: `table_tool`
Use this AFTER finding each speaker's LinkedIn to create a downloadable table of session info. 
If there are multiple instances of the same institution, you only have to write it **once**.
Inputs are structured as follows:

table_tool(
    [
        {
            "names": "Anandi Law; Evelyn Kim; Lord Sarino; Micah Hata; Skai Pan",
            "professional_titles": "President, AACP; Associate Dean for Assessment, College of Pharmacy, Western University of Health Sciences;",
            "institution": "Western Health Sciences",
            "city_state": "Los Angeles, California",
            "title": "Technician Roles in Vaccinations: Impact of California Immunization Registry Access on Vaccine Co‐Administration Rates in Community Pharmacies",
            "dtl": "March 22 \n 1:00 PM - 3:00 PM \n Exhibit Hall D - Music City Center",
            "bio": "https://www.linkedin.com/in/anandi-law-6548b25/"
        },
        {
            "names": "Abby Roth",
            "professional_titles": "Founder/Microbiologist",
            "institution": "Pure Microbiology",
            "city_state": "Macungie, Pennsylvania",
            "title": "BCSCP - K.I.S.S.: Know Important Sampling Standards",
            "dtl": "March 20 \n 8:15 AM - 9:15 AM \n 101AB - Music City Center",
            "bio": "https://www.linkedin.com/in/abbyroth/"
        }
    ]
)

Include:
- Full presenter names (separated by semi-colons)
- Matching professional titles
- Institution(s)
- City/State (Likely found from LinkedIn or Institution, or possibly even the Description)
- Title of presentation
- Date, time, and location in one string
- LinkedIn(s) if you can find it via the linkedin_search_tool, if not **leave blank**

---

#### TOOL: `linkedin_search_tool`
ONLY use if the user explicitly asks you to find a speaker's LinkedIn OR if you are creating a table with the table_tool.

Use the **name, title, and institution** of the presenter.

**Example call**:
{
  "name": "linkedin_search_tool",
  "args": {
    "name": "Jake Paccione",
    "title": "Undergraduate Research Assistant",
    "institution": "Stevens Institute of Technology"
  }
}

If no result is found, reply:  
> "I couldn't find a LinkedIn profile for [name]."

---

### ADDITIONAL GUIDELINES

- Always provide session **date, time (standard time format), and location**
- Mention whether preregistration is required, if `Preregistration: True`
- List **presenters** (from `Presenters` or the `Description`)
- Include **special interest groups** if mentioned

"""

# LLM Agent
def call_llm(state: AgentState) -> AgentState:
    """Function to call the LLM with the current state"""
    MAX_HISTORY = 20
    messages = list(state['messages'])[-MAX_HISTORY:]

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

        # If the table was just created, force rerun
        if t["name"] == "table_tool" and os.path.exists("table.docx"):
            st.session_state["just_made_table"] = True
            st.rerun()


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
    st.set_page_config(
        page_title="Pfizer Conference Planning Agent",
        page_icon="images\pfizer.svg"
    )

    st.markdown("""
    <div style='text-align: center;'>
        <img src='https://upload.wikimedia.org/wikipedia/commons/5/57/Pfizer_%282021%29.svg' width='250' style='margin-bottom: 2px;' />
        <div style='font-size: 40px; font-weight: bold;'>Conference Planning Agent</div>
    </div>
    <hr style='border: none; border-top: 2px solid #ccc; margin-top: 10px; margin-bottom: 50px;' />
    """, unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    for msg in st.session_state["messages"]:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        avatar = "images\person.svg" if isinstance(msg, HumanMessage) else "images\pfizer.svg"
        with st.chat_message(role, avatar=avatar):
            st.write(msg.content)

    if st.session_state.get("just_made_table"):
        with open("table.docx", "rb") as file:
            
            download_success = 'Table created. You can download it below.'

            with st.chat_message("assistant", avatar="images\pfizer.svg"):
                st.write(download_success)
            st.session_state["messages"].append(AIMessage(content=download_success))

            st.download_button(
                label="Download Table",
                data=file,
                file_name="table.docx",
                icon=":material/download:"
            )
        st.session_state["just_made_table"] = False

    user_input = st.chat_input("How can I help you plan a schedule for 2025 Health Conferences?")
    if user_input:
        with st.chat_message("user", avatar="images\person.svg"):
            st.write(user_input)

        st.session_state["messages"].append(HumanMessage(content=user_input))

        state: AgentState = {"messages": st.session_state["messages"]}

        with st.spinner("Thinking..."):
            result = agent.invoke(state, {"recursion_limit": 100})

        with st.chat_message("assistant", avatar="images\pfizer.svg"):
            st.write(result["messages"][-1].content)

        st.session_state["messages"].append(AIMessage(content=result["messages"][-1].content))

running_agent()