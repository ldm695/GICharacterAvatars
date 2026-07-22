"""
Character avatar circle cropping tool.
- Read raw square PNGs from the output/ directory
- Crop to circular PNGs
- Output to output/cropped/
"""

import os
from io import BytesIO
from PIL import Image, ImageDraw

from common import AVATARS_ALL, HOYOWIKI_LABEL, MIHOYO_LABEL, RAW_DIR, CROPPED_DIR

# ===== Config =====
# Supersample factor for the circular mask, used for antialiasing
# (larger = smoother edges, more memory).
SUPERSAMPLE = 4

# Sources (raw files)
SRC_ALL = os.path.join(RAW_DIR, AVATARS_ALL)
SRC_MIHOYO = os.path.join(RAW_DIR, MIHOYO_LABEL)
SRC_HOYOWIKI = os.path.join(RAW_DIR, HOYOWIKI_LABEL)

# Targets (after cropping)
CROP_DIR = CROPPED_DIR
DST_ALL = os.path.join(CROP_DIR, AVATARS_ALL)
DST_MIHOYO = os.path.join(CROP_DIR, MIHOYO_LABEL)
DST_HOYOWIKI = os.path.join(CROP_DIR, HOYOWIKI_LABEL)


def crop_circle(img_data: bytes) -> BytesIO:
    """Crop a square PNG into a circle, preserving the RGBA transparent background.

    The mask is drawn at SUPERSAMPLE times the size then downscaled with LANCZOS
    to remove aliasing on the circular edge.
    """
    img = Image.open(BytesIO(img_data)).convert("RGBA")
    size = min(img.size)
    left = (img.width - size) // 2
    top = (img.height - size) // 2
    img = img.crop((left, top, left + size, top + size))

    big = size * SUPERSAMPLE
    mask = Image.new("L", (big, big), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, big, big), fill=255)
    mask = mask.resize((size, size), Image.Resampling.LANCZOS)

    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    result.paste(img, (0, 0), mask)

    buf = BytesIO()
    result.save(buf, format="PNG")
    buf.seek(0)
    return buf


def process_dir(src_dir: str, dst_dir: str, label: str) -> tuple[int, int]:
    """Process all PNGs in a directory, returning (ok, fail)."""
    if not os.path.isdir(src_dir):
        print(f"  [{label}] source dir not found: {src_dir}")
        return 0, 0

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
        except (OSError, SyntaxError, ValueError) as e:
            print(f"    [{label}] {filename}: crop failed - {e}")
            fail += 1

    return ok, fail


def main():
    print("=" * 50)
    print("  Character Avatar Circle Cropping Tool")
    print("=" * 50)

    tasks = [
        (SRC_ALL, DST_ALL, "avatars_all"),
        (SRC_MIHOYO, DST_MIHOYO, "upload-os-bbs_mihoyo_com"),
        (SRC_HOYOWIKI, DST_HOYOWIKI, "upload-static_hoyoverse_com"),
    ]

    total_ok = total_fail = 0
    for src, dst, label in tasks:
        print(f"\nProcessing [{label}] ...")
        ok, fail = process_dir(src, dst, label)
        total_ok += ok
        total_fail += fail
        print(f"  -> {ok} ok, {fail} fail")

    print(f"\n{'=' * 50}")
    print(f"  Done! Total {total_ok} ok, {total_fail} fail")
    print(f"  Output dir: {CROP_DIR}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
