import os
import json
import re
import shutil
import requests
import subprocess

from exiftool import ExifToolHelper

import utils.logs as logs

GITHUB_REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

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

    Returns:
        None

    Raises:
        Exception: If there is an error saving the file to disk.
    """
    try:
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            logs.log.info(f"Directory {save_dir} did not exist so creating it")
        with open(os.path.join(save_dir, uploaded_file.name), "wb") as f:
            f.write(uploaded_file.getbuffer())
            logs.log.info(f"Upload {uploaded_file.name} saved to disk")
    except Exception as e:
        logs.log.error(f"Error saving upload to disk: {e}")


###################################
#
# Confirm a GitHub Repo Exists
#
###################################


def validate_github_repo(repo: str):
    """
    Validates whether a GitHub repository exists.

    Args:
        repo (str): The name of the GitHub repository.

    Returns:
        True if the repository exists, False otherwise.

    Raises:
        Exception: If there is an error validating the repository.
    """
    if repo is None or not GITHUB_REPO_PATTERN.fullmatch(repo):
        return False

    repo_endpoint = f"https://github.com/{repo}.git"
    try:
        resp = requests.head(repo_endpoint, timeout=10, allow_redirects=True)
        return resp.status_code == 200
    except Exception as err:
        logs.log.warning(f"Unable to validate GitHub repository {repo}: {err}")
        return False


###################################
#
# Clone a GitHub Repo
#
###################################


def clone_github_repo(repo: str):
    """
    Clones a GitHub repository.

    Args:
        repo (str): The name of the GitHub repository.

    Returns:
        True if the repository is cloned successfully, False otherwise.

    Raises:
        Exception: If there is an error cloning the repository.
    """
    if repo is None or not GITHUB_REPO_PATTERN.fullmatch(repo):
        logs.log.error(f"Invalid GitHub repository format: {repo}")
        return False

    repo_endpoint = f"https://github.com/{repo}.git"
    save_dir = os.path.join(os.getcwd(), "data")
    destination = os.path.join(save_dir, repo)

    try:
        os.makedirs(save_dir, exist_ok=True)

        # Ensure retries of the same repo don't fail because a stale checkout exists.
        if os.path.isdir(destination):
            logs.log.info(f"Removing existing repository directory: {destination}")
            shutil.rmtree(destination)

        result = subprocess.run(
            ["git", "clone", "-q", repo_endpoint, destination],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            logs.log.error(
                f"Error cloning {repo} GitHub repo: {result.stderr.strip() or result.stdout.strip()}"
            )
            return False

        logs.log.info(f"Cloned {repo} repo")
        return True
    except Exception as err:
        logs.log.error(f"Error cloning {repo} GitHub repo: {err}")
        return False


###################################
#
# Extract File Metadata
#
###################################


def get_file_metadata(file_path):
    """
    Extracts various metadata for the specified file.

    Args:
        file_path (str): The path to the file.

    Returns:
        A dictionary containing the extracted metadata.

    Raises:
        Exception: If there is an error extracting the metadata.
    """
    try:
        with ExifToolHelper() as et:
            for d in et.get_metadata(file_path):
                return json.dumps(d, indent=2)
    except Exception:
        pass
