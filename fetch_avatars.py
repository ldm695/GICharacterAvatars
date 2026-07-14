# -*- coding: utf-8 -*-
"""
原神角色头像下载脚本（原始数据）
- 从 API 获取角色数据 → 提取 mihoyo_icon / hoyowiki_icon
- 下载原始图片并验证有效性
- 按域名分文件夹输出到 output/
- 圆角裁剪请使用 crop_circle.py
"""

import os
import time
import sys
import requests
from io import BytesIO
from PIL import Image

# ===== 配置 =====
# 项目根目录（脚本所在位置）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

API_URL_TEMPLATE = "https://genshin-db-api.vercel.app/api/v5/characters?query={name}"

API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

CHAR_LIST_FILE = os.path.join(BASE_DIR, "data", "character_names.txt")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TIMEOUT = 5
INTERVAL = 0.1

# API 不识别全名时的降级查询名
NAME_ALIAS = {
    "naganaharayoimiya": "yoimiya",
}


def download_image(url: str) -> bytes | None:
    try:
        resp = requests.get(url, headers=API_HEADERS, timeout=TIMEOUT, allow_redirects=True)
        if resp.status_code != 200:
            return None
        ct = resp.headers.get("Content-Type", "")
        if not ct.startswith("image/") and len(resp.content) < 200:
            return None
        try:
            Image.open(BytesIO(resp.content)).verify()
        except Exception:
            return None
        return resp.content
    except requests.RequestException:
        return None


def fetch_character_data(name: str) -> dict | None:
    # 先尝试原名，失败则尝试别名
    attempts = [name]
    if name in NAME_ALIAS:
        attempts.append(NAME_ALIAS[name])

    for attempt in attempts:
        url = API_URL_TEMPLATE.replace("{name}", attempt)
        try:
            resp = requests.get(url, headers=API_HEADERS, timeout=TIMEOUT)
            if resp.status_code == 200 and resp.text.strip():
                data = resp.json()
                if data and data.get("images"):
                    return data
        except Exception:
            continue
    return None


def main():
    print("=" * 55)
    print("  原神角色头像下载工具")
    print("=" * 55)

    # 读取角色列表
    with open(CHAR_LIST_FILE, "r", encoding="utf-8") as f:
        names = [line.strip() for line in f if line.strip()]

    total = len(names)
    print(f"\n共 {total} 个角色\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    stats = {"mihoyo_ok": 0, "mihoyo_fail": 0, "hoyowiki_ok": 0, "hoyowiki_fail": 0, "api_fail": 0}

    for idx, name in enumerate(names):
        sys.stdout.write(f"\r[{idx+1}/{total}] {name:<30s} ")
        sys.stdout.flush()

        data = fetch_character_data(name)
        if not data:
            print(f"[API 无响应]")
            stats["api_fail"] += 1
            if idx < total - 1:
                time.sleep(INTERVAL)
            continue

        images = data.get("images", {})

        for key, domain_label in [("mihoyo_icon", "upload-os-bbs_mihoyo_com"), ("hoyowiki_icon", "upload-static_hoyoverse_com")]:
            url = images.get(key)
            if not url:
                continue

            save_dir = os.path.join(OUTPUT_DIR, domain_label)
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, f"{name}.png")

            img_data = download_image(url)
            if img_data is None:
                stats[f"{key.split('_')[0]}_fail"] = stats.get(f"{key.split('_')[0]}_fail", 0) + 1
                continue

            try:
                with open(save_path, "wb") as f:
                    f.write(img_data)
                print(f"[{key.split('_')[0]} OK]", end=" ")
                stats[f"{key.split('_')[0]}_ok"] = stats.get(f"{key.split('_')[0]}_ok", 0) + 1
            except Exception:
                print(f"[{key.split('_')[0]} 保存失败]", end=" ")

        print()

        if idx < total - 1:
            time.sleep(INTERVAL)

    print(f"\n{'=' * 55}")
    print(f"  完成！")
    print(f"  mihoyo_icon 成功: {stats.get('mihoyo_ok', 0)}  失败: {stats.get('mihoyo_fail', 0)}")
    print(f"  hoyowiki_icon 成功: {stats.get('hoyowiki_ok', 0)}  失败: {stats.get('hoyowiki_fail', 0)}")
    print(f"  API 无响应: {stats['api_fail']}")
    print(f"  输出目录: {OUTPUT_DIR}")
    print(f"{'=' * 55}")

if __name__ == "__main__":
    main()
