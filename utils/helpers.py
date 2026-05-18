import os
import json
import ipaddress
import re
import shutil
import socket
import requests
import subprocess
from pathlib import Path
from urllib.parse import urljoin, urlparse

from exiftool import ExifToolHelper
import html2text
from llama_index.core import Document

import utils.logs as logs

GITHUB_REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SAFE_UPLOAD_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ -]{0,127}$")
ALLOWED_UPLOAD_EXTENSIONS = {
    ".csv",
    ".docx",
    ".epub",
    ".ipynb",
    ".json",
    ".md",
    ".pdf",
    ".ppt",
    ".pptx",
    ".txt",
}
BLOCKED_HOSTNAMES = {"localhost", "metadata.google.internal"}
MAX_WEBSITE_URLS = 5
MAX_WEBSITE_RESPONSE_BYTES = 5 * 1024 * 1024
MAX_WEBSITE_REDIRECTS = 3
WEBSITE_REQUEST_TIMEOUT = (5, 20)
MAX_UPLOAD_FILES = 10
MAX_UPLOAD_FILE_BYTES = 25 * 1024 * 1024
MAX_TOTAL_UPLOAD_BYTES = 100 * 1024 * 1024
GIT_CLONE_TIMEOUT_SECONDS = 120


def _is_blocked_ip(ip_address: str) -> bool:
    ip = ipaddress.ip_address(ip_address)
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def _validate_public_http_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("Only https URLs are allowed.")
    if parsed.username or parsed.password:
        raise ValueError("URLs with embedded credentials are not allowed.")
    if not parsed.hostname:
        raise ValueError("URL must include a hostname.")

    hostname = parsed.hostname.lower().rstrip(".")
    if hostname in BLOCKED_HOSTNAMES:
        raise ValueError("Local or metadata hostnames are not allowed.")

    try:
        resolved_addresses = socket.getaddrinfo(
            hostname, parsed.port or 443, type=socket.SOCK_STREAM
        )
    except socket.gaierror as err:
        raise ValueError(f"Unable to resolve URL hostname: {hostname}") from err

    for address in resolved_addresses:
        ip_address = address[4][0]
        if _is_blocked_ip(ip_address):
            raise ValueError("URL resolves to a blocked network address.")

    return parsed.geturl()


def validate_website_urls(urls: list[str]) -> list[str]:
    if len(urls) > MAX_WEBSITE_URLS:
        raise ValueError(
            f"At most {MAX_WEBSITE_URLS} websites can be processed at once."
        )

    return [_validate_public_http_url(url) for url in urls]


def load_website_documents(urls: list[str]) -> list[Document]:
    """Fetch website content with SSRF and response-size guardrails."""
    documents = []
    session = requests.Session()

    for url in validate_website_urls(urls):
        current_url = url
        for _ in range(MAX_WEBSITE_REDIRECTS + 1):
            current_url = _validate_public_http_url(current_url)
            response = session.get(
                current_url,
                allow_redirects=False,
                stream=True,
                timeout=WEBSITE_REQUEST_TIMEOUT,
                headers={"User-Agent": "local-rag/website-ingestion"},
            )

            if response.is_redirect:
                location = response.headers.get("Location")
                if not location:
                    raise ValueError(
                        f"Redirect from {current_url} did not include a Location header."
                    )
                current_url = urljoin(current_url, location)
                continue

            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type and "text/plain" not in content_type:
                raise ValueError(
                    f"Unsupported website content type: {content_type or 'unknown'}"
                )

            chunks = []
            total_bytes = 0
            for chunk in response.iter_content(chunk_size=64 * 1024):
                if not chunk:
                    continue
                total_bytes += len(chunk)
                if total_bytes > MAX_WEBSITE_RESPONSE_BYTES:
                    raise ValueError("Website response is too large to process.")
                chunks.append(chunk)

            html = b"".join(chunks).decode(
                response.encoding or "utf-8", errors="replace"
            )
            text = html2text.html2text(html) if "text/html" in content_type else html
            documents.append(Document(text=text, metadata={"source": current_url}))
            break
        else:
            raise ValueError(
                f"Website exceeded {MAX_WEBSITE_REDIRECTS} redirects: {url}"
            )

    return documents


def safe_uploaded_filename(filename: str) -> str:
    if not filename:
        raise ValueError("Uploaded file must have a filename.")
    if "/" in filename or "\\" in filename:
        raise ValueError("Uploaded filename cannot include path separators.")
    if any(ord(char) < 32 for char in filename):
        raise ValueError("Uploaded filename cannot include control characters.")
    if not SAFE_UPLOAD_NAME_PATTERN.fullmatch(filename):
        raise ValueError("Uploaded filename contains unsupported characters.")
    if Path(filename).suffix.lower() not in ALLOWED_UPLOAD_EXTENSIONS:
        raise ValueError("Uploaded file type is not supported.")
    return filename


def upload_destination(save_dir: str, filename: str) -> Path:
    safe_name = safe_uploaded_filename(filename)
    base_dir = Path(save_dir).resolve()
    destination = (base_dir / safe_name).resolve()
    if not destination.is_relative_to(base_dir):
        raise ValueError("Uploaded filename resolves outside the upload directory.")
    return destination


def validate_uploaded_files(uploaded_files: list) -> None:
    if len(uploaded_files) > MAX_UPLOAD_FILES:
        raise ValueError(f"At most {MAX_UPLOAD_FILES} files can be uploaded at once.")

    total_size = 0
    for uploaded_file in uploaded_files:
        safe_uploaded_filename(uploaded_file.name)
        size = getattr(uploaded_file, "size", None)
        if size is None:
            size = len(uploaded_file.getbuffer())
        if size > MAX_UPLOAD_FILE_BYTES:
            raise ValueError(f"{uploaded_file.name} exceeds the per-file upload limit.")
        total_size += size

    if total_size > MAX_TOTAL_UPLOAD_BYTES:
        raise ValueError("Uploaded files exceed the total upload limit.")


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
        destination = upload_destination(save_dir, uploaded_file.name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as f:
            f.write(uploaded_file.getbuffer())
            logs.log.info(f"Upload {uploaded_file.name} saved to disk")
    except Exception as e:
        logs.log.error(f"Error saving upload to disk: {e}")
        raise


###################################
#
# Confirm a GitHub Repo Exists
#
###################################


def normalize_github_repo(repo: str):
    """Normalize owner/repo or a github.com URL into owner/repo."""
    if repo is None:
        raise ValueError("GitHub repository is required.")

    repo = repo.strip()
    parsed = urlparse(repo)
    if parsed.scheme or parsed.netloc:
        if parsed.scheme != "https":
            raise ValueError("GitHub repository URLs must use https.")
        if parsed.netloc.lower() != "github.com":
            raise ValueError("Only github.com repository URLs are supported.")
        path_parts = [part for part in parsed.path.split("/") if part]
        if len(path_parts) != 2:
            raise ValueError("GitHub repository URL must point to owner/repo.")
        owner, repo_name = path_parts
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]
        repo = f"{owner}/{repo_name}"

    if not GITHUB_REPO_PATTERN.fullmatch(repo):
        raise ValueError("Use the format owner/repo or a github.com repository URL.")

    return repo


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
    try:
        repo = normalize_github_repo(repo)
    except ValueError:
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
        The cloned repository directory if successful, False otherwise.

    Raises:
        Exception: If there is an error cloning the repository.
    """
    try:
        repo = normalize_github_repo(repo)
    except ValueError:
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
            ["git", "clone", "--depth", "1", "-q", repo_endpoint, destination],
            check=False,
            capture_output=True,
            text=True,
            timeout=GIT_CLONE_TIMEOUT_SECONDS,
        )
        if result.returncode != 0:
            logs.log.error(
                f"Error cloning {repo} GitHub repo: {result.stderr.strip() or result.stdout.strip()}"
            )
            return False

        logs.log.info(f"Cloned {repo} repo")
        return destination
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
