#!/usr/bin/env python3
"""
Genshin Impact character avatar automation tool - main entry point.

Flow:
  1. Fetch all raw character avatars from the genshin-db API
  2. Merge into avatars_all (mihoyo first -> hoyoverse fallback)
  3. Optional: fetch temporary links (sandrone / lohen etc. from Fandom)
  4. Optional: circle crop -> output/cropped/
"""

import os
import sys
import json
import shutil
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import BASE_DIR, OUTPUT_DIR, RAW_DIR, CROPPED_DIR, FALLBACK_FILE, read_character_names

FETCH_SCRIPT = os.path.join(BASE_DIR, "fetch_avatars.py")
CROP_SCRIPT = os.path.join(BASE_DIR, "crop_circle.py")


def run_script(script: str) -> int:
    """Run a sub-script with the current interpreter, returning its exit code."""
    return subprocess.run([sys.executable, script]).returncode


def confirm(prompt: str) -> bool:
    """Ask the user yes/no, defaulting to no."""
    while True:
        answer = input(f"{prompt} [y/N] ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("", "n", "no"):
            return False
        print("  Please enter y or n")


def merge_raw_icons():
    """Merge raw avatars from per-domain dirs into avatars_all (mihoyo first)."""
    print("\n-- Merging raw avatars into avatars_all --")

    src_dirs = {
        "upload-os-bbs_mihoyo_com": os.path.join(RAW_DIR, "upload-os-bbs_mihoyo_com"),
        "upload-static_hoyoverse_com": os.path.join(RAW_DIR, "upload-static_hoyoverse_com"),
    }
    dst_dir = os.path.join(RAW_DIR, "avatars_all")
    os.makedirs(dst_dir, exist_ok=True)

    # Collect all character names
    all_names = set()
    for d in src_dirs.values():
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.endswith(".png"):
                    all_names.add(f)

    # Copy with mihoyo priority
    for name in sorted(all_names):
        src = os.path.join(src_dirs["upload-os-bbs_mihoyo_com"], name)
        if not os.path.isfile(src):
            src = os.path.join(src_dirs["upload-static_hoyoverse_com"], name)
        dst = os.path.join(dst_dir, name)
        shutil.copy2(src, dst)

    print(f"  Done: {len(all_names)} avatars merged into avatars_all")


def fetch_fallback():
    """Download character avatars from temporary links in fallback_urls.json."""
    print("\n-- Fetching temporary links --")

    if not os.path.isfile(FALLBACK_FILE):
        print("  fallback_urls.json not found, skipping")
        return

    with open(FALLBACK_FILE, encoding="utf-8") as f:
        fallbacks = json.load(f)

    # Filter out non-character entries
    urls = {k: v for k, v in fallbacks.items() if not k.startswith("_")}
    if not urls:
        print("  No valid links, skipping")
        return

    from PIL import Image

    from common import HOYOWIKI_LABEL, download_and_verify

    for name, url in urls.items():
        print(f"  {name}: ", end="", flush=True)

        img_data = download_and_verify(url, timeout=15)
        if img_data is None:
            print("download failed or invalid image")
            continue

        # Save to output/upload-static_hoyoverse_com/ (as a third-party source)
        save_global = os.path.join(RAW_DIR, HOYOWIKI_LABEL, f"{name}.png")
        os.makedirs(os.path.dirname(save_global), exist_ok=True)
        with open(save_global, "wb") as f:
            f.write(img_data)
        print(f"OK ({len(img_data)} bytes)")

        # Fix possible non-PNG encodings such as WebP
        img = Image.open(save_global)
        if img.format != "PNG":
            img.save(save_global, format="PNG")

    print("  Temporary links fetched (re-merging avatars_all)")


def main():
    print("=" * 55)
    print("   Genshin Impact Character Avatar Automation Tool")
    print("   API: github.com/theBowja/genshin-db-api")
    print("=" * 55)
    print(f"\nCharacter list: data/character_names.txt ({len(read_character_names())} characters)")
    print(f"Output dir: {OUTPUT_DIR}/")
    print("  |-- raw/                                raw squares")
    print("  |   |-- avatars_all/                    merged (mihoyo first)")
    print("  |   |-- upload-os-bbs_mihoyo_com/        Miyoushe source")
    print("  |   \\-- upload-static_hoyoverse_com/     HoYoWiki source")
    print("  \\-- cropped/                            circle-cropped (optional)")
    print("      |-- avatars_all/                    merged (mihoyo first)")
    print("      |-- upload-os-bbs_mihoyo_com/        Miyoushe source")
    print("      \\-- upload-static_hoyoverse_com/     HoYoWiki source")

    # -- Step 1: fetch --
    print("\n" + "=" * 55)
    print("Step 1/3: fetch character avatars from the genshin-db API")
    print("=" * 55)
    if confirm("Start fetching?"):
        if run_script(FETCH_SCRIPT) != 0:
            print("\n[!] Errors occurred during fetching, continuing with next steps")
    else:
        print("  Skipped")

    # -- Merge --
    merge_raw_icons()

    # -- Step 2: temporary links --
    print("\n" + "=" * 55)
    print("Step 2/3: fetch temporary links (sandrone / lohen etc. from Fandom)")
    print("=" * 55)
    if confirm("Fetch temporary links?"):
        fetch_fallback()
        merge_raw_icons()  # re-merge
    else:
        print("  Skipped")

    # -- Step 3: crop --
    print("\n" + "=" * 55)
    print("Step 3/3: circle crop -> output/cropped/")
    print("=" * 55)
    if confirm("Run circle crop?"):
        if run_script(CROP_SCRIPT) != 0:
            print("\n[!] Errors occurred during cropping")
    else:
        print("  Skipped")

    # Done
    print("\n" + "=" * 55)
    print("  All done!")
    print(f"  Raw square: {os.path.join(RAW_DIR, 'avatars_all')}/")
    print(f"  Circle-cropped: {os.path.join(CROPPED_DIR, 'avatars_all')}/")
    print("=" * 55)


if __name__ == "__main__":
    main()
