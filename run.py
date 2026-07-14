#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
原神角色头像自动化工具 — 总入口
─────────────────────────────
流程:
  1. 从 genshin-db API 拉取全部角色原始头像
  2. 按 mihoyo 优先 → hoyoverse 兜底整合为 avatars_all
  3. 可选：拉取临时链接（sandrone / lohen 等来自 Fandom）
  4. 可选：圆形裁剪 → output/cropped/
"""

import os
import sys
import json
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

sys.path.insert(0, BASE_DIR)

FETCH_SCRIPT = os.path.join(BASE_DIR, "fetch_avatars.py")
CROP_SCRIPT = os.path.join(BASE_DIR, "crop_circle.py")
FALLBACK_FILE = os.path.join(BASE_DIR, "data", "fallback_urls.json")


def confirm(prompt: str) -> bool:
    """询问用户 yes/no，默认 no"""
    while True:
        answer = input(f"{prompt} [y/N] ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("", "n", "no"):
            return False
        print("  请输入 y 或 n")


def merge_raw_icons():
    """将 domain 分目录的原始头像整合到 avatars_all（mihoyo 优先）"""
    print("\n── 整合原始头像到 avatars_all ──")

    src_dirs = {
        "upload-os-bbs_mihoyo_com": os.path.join(OUTPUT_DIR, "upload-os-bbs_mihoyo_com"),
        "upload-static_hoyoverse_com": os.path.join(OUTPUT_DIR, "upload-static_hoyoverse_com"),
    }
    dst_dir = os.path.join(OUTPUT_DIR, "avatars_all")
    os.makedirs(dst_dir, exist_ok=True)

    # 收集所有角色名
    all_names = set()
    for d in src_dirs.values():
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.endswith(".png"):
                    all_names.add(f)

    # mihoyo 优先拷贝
    for name in sorted(all_names):
        src = os.path.join(src_dirs["upload-os-bbs_mihoyo_com"], name)
        if not os.path.isfile(src):
            src = os.path.join(src_dirs["upload-static_hoyoverse_com"], name)
        dst = os.path.join(dst_dir, name)
        shutil.copy2(src, dst)

    print(f"  完成：{len(all_names)} 个头像已整合到 avatars_all")


def fetch_fallback():
    """从 fallback_urls.json 下载临时链接的角色头像"""
    print("\n── 拉取临时链接 ──")

    if not os.path.isfile(FALLBACK_FILE):
        print("  未找到 fallback_urls.json，跳过")
        return

    with open(FALLBACK_FILE, encoding="utf-8") as f:
        fallbacks = json.load(f)

    # 过滤非角色条目
    urls = {k: v for k, v in fallbacks.items() if not k.startswith("_")}
    if not urls:
        print("  无有效链接，跳过")
        return

    import requests
    from io import BytesIO
    from PIL import Image

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    for name, url in urls.items():
        print(f"  {name}: ", end="", flush=True)
        try:
            resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            if resp.status_code != 200:
                print(f"HTTP {resp.status_code}")
                continue

            # 验证图片
            try:
                Image.open(BytesIO(resp.content)).verify()
            except Exception:
                print("无效图片")
                continue

            # 保存到 output/upload-static_hoyoverse_com/（作为第三方来源）
            save_global = os.path.join(OUTPUT_DIR, "upload-static_hoyoverse_com", f"{name}.png")
            os.makedirs(os.path.dirname(save_global), exist_ok=True)
            with open(save_global, "wb") as f:
                f.write(resp.content)
            print(f"OK ({len(resp.content)} bytes)")
            # 修复可能的 WebP 后缀
            img = Image.open(save_global)
            if img.format != "PNG":
                img.save(save_global, format="PNG")
        except Exception as e:
            print(f"失败 — {e}")

    print("  临时链接拉取完成（重新整合 avatars_all）")


def main():
    print("=" * 55)
    print("   原神角色头像自动化工具")
    print("   API: github.com/theBowja/genshin-db-api")
    print("=" * 55)
    print(f"\n角色列表: data/character_names.txt ({sum(1 for _ in open(os.path.join(BASE_DIR, 'data', 'character_names.txt'), encoding='utf-8') if _.strip())} 个角色)")
    print(f"输出目录: {OUTPUT_DIR}/")
    print(f"  ├── avatars_all/        原始方形（整合版，mihoyo 优先）")
    print(f"  ├── upload-os-bbs_mihoyo_com/  米游社源")
    print(f"  ├── upload-static_hoyoverse_com/  HoYoWiki 源")
    print(f"  └── cropped/               圆形裁剪版（可选）")

    # ── 步骤 1：拉取 ──
    print("\n" + "=" * 55)
    print("步骤 1/3：从 genshin-db API 拉取角色头像")
    print("=" * 55)
    if confirm("开始拉取？"):
        ret = os.system(f'"{sys.executable}" "{FETCH_SCRIPT}"')
        if ret != 0:
            print("\n⚠ 拉取过程出现错误，继续后续步骤")
    else:
        print("  跳过")

    # ── 整合 ──
    merge_raw_icons()

    # ── 步骤 2：临时链接 ──
    print("\n" + "=" * 55)
    print("步骤 2/3：拉取临时链接（sandrone / lohen 等 Fandom 来源）")
    print("=" * 55)
    if confirm("拉取临时链接？"):
        fetch_fallback()
        merge_raw_icons()  # 重新整合
    else:
        print("  跳过")

    # ── 步骤 3：裁剪 ──
    print("\n" + "=" * 55)
    print("步骤 3/3：圆形裁剪 → output/cropped/")
    print("=" * 55)
    if confirm("执行圆形裁剪？"):
        ret = os.system(f'"{sys.executable}" "{CROP_SCRIPT}"')
        if ret != 0:
            print("\n⚠ 裁剪过程出现错误")
    else:
        print("  跳过")

    # 完成
    print("\n" + "=" * 55)
    print("  全部完成！")
    print(f"  原始方形: {OUTPUT_DIR}/avatars_all/")
    print(f"  圆形裁剪: {os.path.join(OUTPUT_DIR, 'cropped', 'avatars_all')}/")
    print("=" * 55)


if __name__ == "__main__":
    main()
