import streamlit as st

import utils.rag_pipeline as rag

from llama_index.readers.web import SimpleWebPageReader
from urllib.parse import urlparse


def website():
    # if st.session_state["selected_model"] is not None:
    #     st.text_input(
    #         "Clone a website",
    #         placeholder="https://ollama.com/blog",
    #     )
    #     st.button(
    #         "Copy",
    #     )
    # else:
    #     st.text_input(
    #         "Clone a website",
    #         placeholder="https://ollama.com/blog",
    #         disabled=True,
    #     )
    #     st.button(
    #         "Copy",
    #         disabled=True,
    #     )

    # css_example = '''
    # I'm importing the font-awesome icons as a stylesheet!
    # <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">

    # <i class="fa-brands fa-github"></i>
    # <i class="fa-solid fa-dragon"></i>
    # <i class="fa-solid fa-paw"></i>
    # '''

    # st.write(css_example, unsafe_allow_html=True)

    def ensure_https(url):
        parsed = urlparse(url)
    
        if not bool(parsed.scheme):
            return f"https://{url}"
    
        return url

    st.write("Enter a Website")
    col1, col2 = st.columns([1,.2])
    with col1:
        new_website = st.text_input("Enter a Website", label_visibility="collapsed")
    with col2:
        add_button = st.button(u"➕")

    # If the add button is clicked, append the new website to our list
    if add_button and new_website != '':
        st.session_state['websites'].append(ensure_https(new_website))
        st.session_state['websites'] = sorted(set(st.session_state['websites']))
    
    if st.session_state['websites'] != []:
        st.markdown(f"<p>Website(s)</p>", unsafe_allow_html=True)
        for site in st.session_state['websites']:
            st.caption(f"- {site}")
        st.write("")

        process_button = st.button("Process", key="process_website")
        
        if process_button:
            documents = SimpleWebPageReader(html_to_text=True).load_data(
                st.session_state['websites']
            )

            if len(documents) > 0:
                st.session_state["documents"] = documents

                with st.spinner("Processing..."):
                    # Initiate the RAG pipeline, providing documents to be saved on disk if necessary
                    error = rag.rag_pipeline()

                    # Display errors (if any) or proceed
                    if error is not None:
                        st.exception(error)
                    else:
                        st.write("Site processing completed. Let's chat! 😎")
