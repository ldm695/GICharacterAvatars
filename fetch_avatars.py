"""
Genshin Impact character avatar downloader (raw data).
- Fetch character data from the API -> extract mihoyo_icon / hoyowiki_icon
- Download raw images and verify validity (concurrent + connection reuse)
- Output to output/, grouped by domain
- For circle cropping, use crop_circle.py
"""

import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from common import (
    API_HEADERS,
    HOYOWIKI_LABEL,
    MIHOYO_LABEL,
    RAW_DIR,
    DEFAULT_TIMEOUT,
    download_and_verify,
    make_session,
    read_character_names,
)

# ===== Config =====
API_URL_TEMPLATE = "https://genshin-db-api.vercel.app/api/v5/characters?query={name}"
MAX_WORKERS = 8

# Fallback query names for when the API does not recognize the full name
NAME_ALIAS = {
    "naganaharayoimiya": "yoimiya",
}

# icon key -> (output subdirectory, stats short name)
ICON_SOURCES = [
    ("mihoyo_icon", MIHOYO_LABEL, "mihoyo"),
    ("hoyowiki_icon", HOYOWIKI_LABEL, "hoyowiki"),
]


def fetch_character_data(name: str, session: requests.Session) -> dict | None:
    """Query character data; if the full name fails, try the alias."""
    attempts = [name]
    if name in NAME_ALIAS:
        attempts.append(NAME_ALIAS[name])

    for attempt in attempts:
        url = API_URL_TEMPLATE.replace("{name}", attempt)
        try:
            resp = session.get(url, headers=API_HEADERS, timeout=DEFAULT_TIMEOUT)
            if resp.status_code == 200 and resp.text.strip():
                data = resp.json()
                if data and data.get("images"):
                    return data
        except Exception:
            continue
    return None


def process_character(name: str, session: requests.Session) -> dict:
    """
    Process a single character: query data -> download each source icon -> save.
    Returns a result dict for the main thread to aggregate (workers do not mutate shared state).
    """
    result = {"name": name, "api_fail": False}

    data = fetch_character_data(name, session)
    if not data:
        result["api_fail"] = True
        return result

    images = data.get("images", {})
    for key, label, tag in ICON_SOURCES:
        url = images.get(key)
        if not url:
            continue

        img_data = download_and_verify(url, session)
        if img_data is None:
            result[tag] = "fail"
            continue

        save_path = os.path.join(RAW_DIR, label, f"{name}.png")
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        try:
            with open(save_path, "wb") as f:
                f.write(img_data)
            result[tag] = "ok"
        except Exception:
            result[tag] = "save_fail"

    return result


def main():
    print("=" * 55)
    print("  Genshin Impact Character Avatar Downloader")
    print("=" * 55)

    names = read_character_names()
    total = len(names)
    print(f"\n{total} characters, concurrency {MAX_WORKERS}\n")

    os.makedirs(RAW_DIR, exist_ok=True)

    stats = {"mihoyo_ok": 0, "mihoyo_fail": 0, "hoyowiki_ok": 0, "hoyowiki_fail": 0, "api_fail": 0}
    session = make_session(pool_maxsize=MAX_WORKERS * 2)
    print_lock = threading.Lock()
    done = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_character, name, session): name for name in names}

        for future in as_completed(futures):
            name = futures[future]
            result = future.result()
            done += 1

            if result.get("api_fail"):
                stats["api_fail"] += 1
                tags = "[API no response]"
            else:
                parts = []
                for _, _, tag in ICON_SOURCES:
                    outcome = result.get(tag)
                    if outcome == "ok":
                        stats[f"{tag}_ok"] += 1
                        parts.append(f"[{tag} OK]")
                    elif outcome == "fail":
                        stats[f"{tag}_fail"] += 1
                        parts.append(f"[{tag} FAIL]")
                    elif outcome == "save_fail":
                        parts.append(f"[{tag} SAVE FAIL]")
                tags = " ".join(parts) if parts else "[no icon]"

            with print_lock:
                print(f"[{done}/{total}] {name:<30s} {tags}")

    print(f"\n{'=' * 55}")
    print("  Done!")
    print(f"  mihoyo_icon ok: {stats['mihoyo_ok']}  fail: {stats['mihoyo_fail']}")
    print(f"  hoyowiki_icon ok: {stats['hoyowiki_ok']}  fail: {stats['hoyowiki_fail']}")
    print(f"  API no response: {stats['api_fail']}")
    print(f"  Output dir: {RAW_DIR}")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()
