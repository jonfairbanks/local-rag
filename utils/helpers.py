import os

import streamlit as st

###################################
#
# Save File Upload to Disk
#
###################################


def save_uploaded_file(uploaded_file: bytes, save_dir: str):
    """
    Saves the uploaded file to the specified directory.

    Args:
        uploaded_file (BytesIO): The uploaded file content.
        save_dir (str): The directory where the file will be saved.
    """
    with open(os.path.join(save_dir, uploaded_file.name), "wb") as f:
        f.write(uploaded_file.getbuffer())


###################################
#
# Process GitHub Repo
#
###################################


def process_github_repo(repo: str):
    """
    Processes a GitHub repository.

    Parameters:
        repo (str): The name of the GitHub repository.
    """
    print(repo)  # Doesn't work?
    github_endpoint = "https://github.com/" + st.session_state.github_repo
    print(github_endpoint)
    return
