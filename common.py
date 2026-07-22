"""
Shared constants and utility functions.

Reused by fetch_avatars.py / crop_circle.py / run.py to avoid duplicating
paths, request headers, and download/validation logic across modules.
"""

import os
from io import BytesIO

import requests
from requests.adapters import HTTPAdapter
from PIL import Image

# ===== Paths =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# Output is grouped into two roots: raw (original squares) and cropped (circles).
RAW_DIR = os.path.join(OUTPUT_DIR, "raw")
CROPPED_DIR = os.path.join(OUTPUT_DIR, "cropped")

CHAR_LIST_FILE = os.path.join(DATA_DIR, "character_names.txt")
FALLBACK_FILE = os.path.join(DATA_DIR, "fallback_urls.json")

# ===== Domain -> output subdirectory label =====
MIHOYO_LABEL = "upload-os-bbs_mihoyo_com"
HOYOWIKI_LABEL = "upload-static_hoyoverse_com"
AVATARS_ALL = "avatars_all"

# ===== Request =====
API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

DEFAULT_TIMEOUT = 5


def make_session(pool_maxsize: int = 16) -> requests.Session:
    """Create a Session with connection pooling for shared concurrent downloads."""
    session = requests.Session()
    session.headers.update(API_HEADERS)
    adapter = HTTPAdapter(
        pool_connections=pool_maxsize, pool_maxsize=pool_maxsize
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def read_character_names() -> list[str]:
    """Read the list of character English names, ignoring blank lines."""
    with open(CHAR_LIST_FILE, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def download_and_verify(
    url: str, session: requests.Session | None = None, timeout: int = DEFAULT_TIMEOUT
) -> bytes | None:
    """
    Download an image and verify it is a decodable, valid image. Returns None on failure.
    - Non-200 status, content too small, or undecodable by PIL -> treated as invalid
    - Content-Type is not relied upon (some image hosts return octet-stream);
      actual decoding is the source of truth.
    """
    client = session or requests
    try:
        resp = client.get(
            url, headers=API_HEADERS, timeout=timeout, allow_redirects=True
        )
        if resp.status_code != 200:
            return None
        if len(resp.content) < 200:
            return None
        try:
            Image.open(BytesIO(resp.content)).verify()
        except (OSError, SyntaxError, ValueError):
            return None
        return resp.content
    except requests.RequestException:
        return None
