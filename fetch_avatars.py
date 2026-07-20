# -*- coding: utf-8 -*-
"""
原神角色头像下载脚本（原始数据）
- 从 API 获取角色数据 → 提取 mihoyo_icon / hoyowiki_icon
- 下载原始图片并验证有效性（并发 + 连接复用）
- 按域名分文件夹输出到 output/
- 圆角裁剪请使用 crop_circle.py
"""

import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from common import (
    API_HEADERS,
    HOYOWIKI_LABEL,
    MIHOYO_LABEL,
    OUTPUT_DIR,
    DEFAULT_TIMEOUT,
    download_and_verify,
    make_session,
    read_character_names,
)

# ===== 配置 =====
API_URL_TEMPLATE = "https://genshin-db-api.vercel.app/api/v5/characters?query={name}"
MAX_WORKERS = 8

# API 不识别全名时的降级查询名
NAME_ALIAS = {
    "naganaharayoimiya": "yoimiya",
}

# 图标 key → (输出子目录, 统计短名)
ICON_SOURCES = [
    ("mihoyo_icon", MIHOYO_LABEL, "mihoyo"),
    ("hoyowiki_icon", HOYOWIKI_LABEL, "hoyowiki"),
]


def fetch_character_data(name: str, session: requests.Session) -> dict | None:
    """查询角色数据，全名失败则尝试别名。"""
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
    处理单个角色：查数据 → 下载各来源图标 → 保存。
    返回结果字典，供主线程汇总统计（不在 worker 内改共享状态）。
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

        save_path = os.path.join(OUTPUT_DIR, label, f"{name}.png")
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
    print("  原神角色头像下载工具")
    print("=" * 55)

    names = read_character_names()
    total = len(names)
    print(f"\n共 {total} 个角色，并发 {MAX_WORKERS}\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

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
                tags = "[API 无响应]"
            else:
                parts = []
                for _, _, tag in ICON_SOURCES:
                    outcome = result.get(tag)
                    if outcome == "ok":
                        stats[f"{tag}_ok"] += 1
                        parts.append(f"[{tag} OK]")
                    elif outcome == "fail":
                        stats[f"{tag}_fail"] += 1
                        parts.append(f"[{tag} 失败]")
                    elif outcome == "save_fail":
                        parts.append(f"[{tag} 保存失败]")
                tags = " ".join(parts) if parts else "[无图标]"

            with print_lock:
                print(f"[{done}/{total}] {name:<30s} {tags}")

    print(f"\n{'=' * 55}")
    print("  完成！")
    print(f"  mihoyo_icon 成功: {stats['mihoyo_ok']}  失败: {stats['mihoyo_fail']}")
    print(f"  hoyowiki_icon 成功: {stats['hoyowiki_ok']}  失败: {stats['hoyowiki_fail']}")
    print(f"  API 无响应: {stats['api_fail']}")
    print(f"  输出目录: {OUTPUT_DIR}")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()
