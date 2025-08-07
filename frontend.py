import streamlit as st
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage, AIMessage
import pandas as pd
from io import StringIO
import streamlit.components.v1 as components


def main():
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

    with st.sidebar:
        uploaded_file = st.file_uploader("Upload a Conference PDF:", type=["pdf"], )

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

        with st.chat_message("assistant", avatar="images\pfizer.svg"):
            st.write(user_input)

        st.session_state["messages"].append(AIMessage(content=user_input))

    if uploaded_file:
        st.success("File uploaded!")

main()