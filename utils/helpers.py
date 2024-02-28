import os
import requests
import subprocess

import streamlit as st

import utils.logs as logs

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
    try:
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        with open(os.path.join(save_dir, uploaded_file.name), "wb") as f:
            f.write(uploaded_file.getbuffer())
    except Exception as e:
        logs.log.info(f"Error saving upload to disk: {e}")


###################################
#
# Confirm a GitHub Repo Exists
#
###################################


def validate_github_repo(repo: str):
    repo_endpoint = "https://github.com/" + repo + ".git"
    resp = requests.head(repo_endpoint)
    if resp.status_code() == 200:
        return True
    else:
        return False


###################################
#
# Clone a GitHub Repo
#
###################################


def clone_github_repo(repo: str):
    """
    Clones a GitHub repository.

    Parameters:
        repo (str): The name of the GitHub repository.
    """
    repo_endpoint = "https://github.com/" + repo + ".git"
    if repo_endpoint is not None:
        save_dir = os.getcwd() + "/data"
        clone_command = f"git clone -q {repo_endpoint} {save_dir}/{repo}"
        try:
            subprocess.run(clone_command, shell=True)
            logs.log.info(f"Cloned {repo} repo")
            return True
        except Exception as e:
            Exception(f"Error cloning {repo} GitHub repo: {e}")
            return False

    else:
        Exception(f"Failed to process GitHub repo {st.session_state['github_repo']}")
        return False
