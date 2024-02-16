import streamlit as st

###################################
#
# Process Local File
#
###################################

def process_local_file(file: str):
    print(file)
    return

###################################
#
# Process GitHub Repo
#
###################################

def process_github_repo(repo: str):
    print(repo) # Doesn't work?
    github_endpoint = "https://github.com/" + st.session_state.github_repo
    print(github_endpoint)
    return