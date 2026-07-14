# -*- coding: utf-8 -*-
"""
角色头像圆形裁剪工具
- 读取 output/ 目录的原始方形 PNG
- 裁剪为圆形 PNG
- 输出到 output/cropped/
"""

import os
from io import BytesIO
from PIL import Image, ImageDraw

# ===== 配置 =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, "output")

# 源（原始文件）
SRC_ALL = os.path.join(OUT_DIR, "avatars_all")
SRC_MIHOYO = os.path.join(OUT_DIR, "upload-os-bbs_mihoyo_com")
SRC_HOYOWIKI = os.path.join(OUT_DIR, "upload-static_hoyoverse_com")

# 目标（裁剪后）
CROP_DIR = os.path.join(OUT_DIR, "cropped")
DST_ALL = os.path.join(CROP_DIR, "avatars_all")
DST_MIHOYO = os.path.join(CROP_DIR, "upload-os-bbs_mihoyo_com")
DST_HOYOWIKI = os.path.join(CROP_DIR, "upload-static_hoyoverse_com")


def crop_circle(img_data: bytes) -> BytesIO:
    """将方形 PNG 裁剪为圆形，保留 RGBA 透明背景"""
    img = Image.open(BytesIO(img_data)).convert("RGBA")
    size = min(img.size)
    left = (img.width - size) // 2
    top = (img.height - size) // 2
    img = img.crop((left, top, left + size, top + size))

    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)

    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    result.paste(img, (0, 0), mask)

    buf = BytesIO()
    result.save(buf, format="PNG")
    buf.seek(0)
    return buf


def process_dir(src_dir: str, dst_dir: str, label: str) -> tuple[int, int]:
    """处理一个目录下的所有 PNG，返回 (成功, 失败)"""
    if not os.path.isdir(src_dir):
        print(f"  [{label}] 源目录不存在: {src_dir}")
        return (0, 0)

    os.makedirs(dst_dir, exist_ok=True)
    ok = fail = 0
    files = sorted(f for f in os.listdir(src_dir) if f.endswith(".png"))

    for filename in files:
        src_path = os.path.join(src_dir, filename)
        dst_path = os.path.join(dst_dir, filename)

        try:
            with open(src_path, "rb") as f:
                raw_data = f.read()
            circle_buf = crop_circle(raw_data)
            with open(dst_path, "wb") as f:
                f.write(circle_buf.getvalue())
            ok += 1
        except Exception as e:
            print(f"    [{label}] {filename}: 裁剪失败 — {e}")
            fail += 1

    return (ok, fail)


def main():
    print("=" * 50)
    print("  角色头像圆形裁剪工具")
    print("=" * 50)

    tasks = [
        (SRC_ALL, DST_ALL, "avatars_all"),
        (SRC_MIHOYO, DST_MIHOYO, "upload-os-bbs_mihoyo_com"),
        (SRC_HOYOWIKI, DST_HOYOWIKI, "upload-static_hoyoverse_com"),
    ]

    total_ok = total_fail = 0
    for src, dst, label in tasks:
        print(f"\n处理 [{label}] ...")
        ok, fail = process_dir(src, dst, label)
        total_ok += ok
        total_fail += fail
        print(f"  -> {ok} 成功, {fail} 失败")

    print(f"\n{'=' * 50}")
    print(f"  完成！总计 {total_ok} 成功, {total_fail} 失败")
    print(f"  输出目录: {CROP_DIR}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
