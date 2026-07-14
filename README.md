# Genshin Character Icons

原神角色头像下载 & 裁剪工具 — 从 [genshin-db-api](https://github.com/theBowja/genshin-db-api) 获取角色头像，可选裁剪为圆形 PNG。

## 快速开始

```bash
pip install -r requirements.txt
python run.py
```

`run.py` 会依次询问：
1. **拉取原始头像** — 从 genshin-db API 下载全部角色
2. **拉取临时链接** — 补档 sandrone/lohen 等 API 无图的角色（来自 Fandom Wiki）
3. **圆形裁剪** — 将原始方形头像裁剪为圆形 → `output/cropped/`

## 目录结构

```
character-avatars/
├── run.py                               # 总入口（自动化流程）
├── fetch_avatars.py                  # 原始头像下载（0.1s 间隔，5s 超时）
├── crop_circle.py                       # 圆形裁剪（独立步骤）
├── gen_avatar_sql.py                    # 生成 SQL UPDATE 语句
├── avatar_mapping.json          # 角色名 → 文件名映射
├── data/
│   ├── character_names.txt              # 118 个可玩角色英文名
│   └── fallback_urls.json               # 临时/备用链接（可能随版本变动）
├── requirements.txt
└── output/
    ├── avatars_all/                  # 原始方形（整合版，mihoyo 优先）
    ├── upload-os-bbs_mihoyo_com/        # 米游社源
    ├── upload-static_hoyoverse_com/     # HoYoWiki 源
    └── cropped/                         # 圆形裁剪版（由 crop_circle.py 生成）
        ├── avatars_all/
        ├── upload-os-bbs_mihoyo_com/
        └── upload-static_hoyoverse_com/
```

## 分步使用

```bash
# 1. 下载原始头像
python fetch_avatars.py

# 2. 整合（mihoyo 优先 → hoyoverse 兜底）
python -c "import os, shutil; O='output'; [shutil.copy2(os.path.join(d,f),os.path.join(O,'avatars_all',f)) for d in [os.path.join(O,'upload-os-bbs_mihoyo_com'),os.path.join(O,'upload-static_hoyoverse_com')] if os.path.isdir(d) for f in os.listdir(d) if f.endswith('.png') and not os.path.isfile(os.path.join(O,'avatars_all',f))]"

# 3. 裁剪为圆形
python crop_circle.py
```

## 说明

- 角色列表截至原神 **6.7** 版本，共 **118** 个可玩角色
- API: [genshin-db-api](https://github.com/theBowja/genshin-db-api) (genshin-db v5)
- `fetch_avatars.py` 每 0.1 秒请求一个角色，超时 5 秒
- 优先使用 `mihoyo_icon`，兜底使用 `hoyowiki_icon`
- aether/lumine（旅行者）使用米游社源，HoYoWiki 共享源合并为 `traveler.png`
- aloy（跨界角色）API 有数据
- sandrone（桑多涅）API 无图标字段，需从 fallback_urls.json 补档
- lohen（HoYoWiki 图标可能变动）也列在 fallback_urls.json

## 数据来源

- [genshin-db-api](https://github.com/theBowja/genshin-db-api) — 角色数据与图标 URL
- [Genshin Impact Fandom Wiki](https://genshin-impact.fandom.com/wiki/Character) — 备用的 sandrone/lohen 图标
