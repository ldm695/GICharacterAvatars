# Genshin Character Icons

原神角色头像下载 & 裁剪工具 — 从 genshin-db API 获取角色头像，可选裁剪为圆形 PNG。

## 架构

```
fetch_char_icons.py    # 下载原始头像（无处理）→ output/raw/
       ↓
crop_circle.py         # 圆形裁剪（从 raw/ 读取 → 输出）
       ↓
output/char_icons_all/ # 最终圆形裁剪头像（供 App 使用）
```

## 目录结构

```
gi-character-avatars/
├── fetch_char_icons.py          # 原始头像下载（0.1s 间隔，5s 超时）
├── crop_circle.py               # 圆形裁剪（独立步骤）
├── gen_avatar_sql.py            # 生成 SQL UPDATE 语句
├── character_icon_mapping.json  # 角色名 → 文件名映射
├── data/character_names.txt     # 118 个可玩角色英文名
├── requirements.txt
└── output/
    ├── raw/                              # 原始方形 PNG（下载产物）
    │   ├── char_icons_all/               #   113 张整合版
    │   ├── upload-os-bbs_mihoyo_com/     #   65 张（米游社源）
    │   └── upload-static_hoyoverse_com/  #   113 张（HoYoWiki 源）
    ├── char_icons_all/                   # 圆形裁剪版（117 张，含旅行者/Aloy 本地归档）
    ├── upload-os-bbs_mihoyo_com/         # 圆形裁剪 65 张
    └── upload-static_hoyoverse_com/      # 圆形裁剪 113 张
```

## 使用

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 下载原始头像（存到 output/raw/）
python fetch_char_icons.py

# 3. 整合原始头像（mihoyo 优先 → hoyowiki 兜底）
python -c "import os,shutil; B='output/raw'; A=os.path.join(B,'char_icons_all'); M=os.path.join(B,'upload-os-bbs_mihoyo_com'); H=os.path.join(B,'upload-static_hoyoverse_com'); os.makedirs(A,exist_ok=True); [shutil.copy2(os.path.join(d,f),os.path.join(A,f)) for d in [M,H] if os.path.isdir(d) for f in os.listdir(d) if f.endswith('.png') and not os.path.isfile(os.path.join(A,f))]"

# 4. 裁剪为圆形（从 raw/ 读取 → 输出到 output/）
python crop_circle.py
```

## 说明

- 角色列表截至原神 **6.7** 版本，共 **118** 个可玩角色
- API: [genshin-db](https://github.com/theBowja/genshin-db)
- `fetch_char_icons.py` 每 0.1 秒请求一个角色，超时 5 秒
- 优先使用 `mihoyo_icon`，兜底使用 `hoyowiki_icon`
- aether/lumine（旅行者）和 aloy（跨界角色）API 无数据，使用本地归档
- sandrone（桑多涅）API 有数据但无图标字段，跳过
