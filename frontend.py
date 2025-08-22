import streamlit as st
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage, AIMessage
import pandas as pd
from io import StringIO
import streamlit.components.v1 as components
import pymupdf
from pypdf import PdfReader
import add_csv_to_chroma


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
        api_key = st.text_input(label="Google Gemini API Key:",type="password", icon=":material/passkey:")

        uploaded_file = st.file_uploader("Upload a Conference PDF:", type=["pdf"])

        if uploaded_file:

            conference_title = st.text_input(label="Please input the Conference Title:")
            conference_year = st.text_input(label="Please input the Conference Year:")

            if conference_title and conference_year:
                reader = PdfReader(uploaded_file)

                full_chunks = []
                for page in reader.pages:
                    text = page.extract_text()
                    chunk = f"""
Conference: {conference_title}
Year: {conference_year}

{text}
                    """
                    full_chunks.append(chunk)
                if full_chunks:
                    embeddings = add_csv_to_chroma.embedder.encode(full_chunks)
                    add_csv_to_chroma.collection.add(
                        documents=full_chunks,
                        embeddings=embeddings,
                        ids=[f"session_{i}" for i in range(len(full_chunks))],
                        metadatas=[{"conference": conference_title} for _ in full_chunks]
                    )
                print(f"Database population from {conference_title} complete.")

                st.success("File uploaded!")

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

main()



# PymuPDF

#         def flags_decomposer(flags):
#             """Make font flags human readable."""
#             l = []
#             if flags & 2 ** 0:
#                 l.append("superscript")
#             if flags & 2 ** 1:
#                 l.append("italic")
#             if flags & 2 ** 2:
#                 l.append("serifed")
#             else:
#                 l.append("sans")
#             if flags & 2 ** 3:
#                 l.append("monospaced")
#             else:
#                 l.append("proportional")
#             if flags & 2 ** 4:
#                 l.append("bold")
#             return ", ".join(l)

        
#         uploaded_file = st.file_uploader("Upload a Conference PDF:", type=["pdf"])

#         if uploaded_file:
#             bytes = uploaded_file.read()

#             doc = pymupdf.open(stream=bytes, filetype="pdf")
#             page = doc[0]

#             # read page text as a dictionary, suppressing extra spaces in CJK fonts
#             blocks = page.get_text("dict", flags=11)["blocks"]
#             for b in blocks:  # iterate through the text blocks
#                 for l in b["lines"]:  # iterate through the text lines
#                     for s in l["spans"]:  # iterate through the text spans
#                         print("")
#                         if (s["text"]) == ' ':
#                             continue
#                         font_properties = "Font: '%s' (%s), size %g, color #%06x" % (
#                             s["font"],  # font name
#                             flags_decomposer(s["flags"]),  # readable font flags
#                             s["size"],  # font size
#                             s["color"],  # font color
#                         )
#                         print("Text: '%s'" % s["text"])  # simple print of text
#                         print(font_properties)