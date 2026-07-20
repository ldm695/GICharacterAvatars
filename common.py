# -*- coding: utf-8 -*-
"""
公共常量与工具函数
─────────────────
被 fetch_avatars.py / crop_circle.py / run.py 复用，避免路径、请求头、
下载校验逻辑在多处重复。
"""

import os
from io import BytesIO

import requests
from PIL import Image

# ===== 路径 =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

CHAR_LIST_FILE = os.path.join(DATA_DIR, "character_names.txt")
FALLBACK_FILE = os.path.join(DATA_DIR, "fallback_urls.json")

# ===== 域名 → 输出子目录标签 =====
MIHOYO_LABEL = "upload-os-bbs_mihoyo_com"
HOYOWIKI_LABEL = "upload-static_hoyoverse_com"
AVATARS_ALL = "avatars_all"

# ===== 请求 =====
API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

DEFAULT_TIMEOUT = 5


def make_session(pool_maxsize: int = 16) -> requests.Session:
    """创建带连接池复用的 Session，供并发下载共享。"""
    session = requests.Session()
    session.headers.update(API_HEADERS)
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=pool_maxsize, pool_maxsize=pool_maxsize
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def read_character_names() -> list[str]:
    """读取角色英文名列表，忽略空行。"""
    with open(CHAR_LIST_FILE, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def download_and_verify(
    url: str, session: requests.Session | None = None, timeout: int = DEFAULT_TIMEOUT
) -> bytes | None:
    """
    下载图片并验证其为可解码的有效图片。失败返回 None。
    - 状态码非 200、内容过小、无法被 PIL 解码 → 判定无效
    - Content-Type 不作强依赖（部分图床返回 octet-stream），以真实解码为准
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
        except Exception:
            return None
        return resp.content
    except requests.RequestException:
        return None
