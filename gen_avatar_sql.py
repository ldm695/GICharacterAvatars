import json
import re
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 主项目 server 与 character-avatars 平级，位于 GINote/ 下
DB_DIR = os.path.normpath(
    os.path.join(BASE_DIR, '..', 'gi-note-server', 'src', 'main', 'resources', 'db')
)

with open(os.path.join(BASE_DIR, 'avatar_mapping.json'), encoding='utf-8') as f:
    mapping = json.load(f)

seedpath = os.path.join(DB_DIR, 'seed.sql')
if not os.path.isfile(seedpath):
    raise SystemExit(f'找不到 seed.sql: {seedpath}\n请确认主项目路径（GINote/gi-note-server）。')
# UUID 迁移后 id 为 md5('character:ABBR')::uuid，不再是整数。
# 用 abbr 作为定位键（seed 里 id 本身也由 abbr 派生），name 用于查映射。
pattern = re.compile(
    r"INSERT INTO characters \(id, name, abbr, rarity, release_date, status\) VALUES "
    r"\([^,]+, '([^']+)', '([^']+)',"
)

# abbr -> name
chars = {}
with open(seedpath, encoding='utf-8') as f:
    for line in f:
        m = pattern.search(line)
        if m:
            chars[m.group(2)] = m.group(1)

lines = ['-- avatar_url 写入脚本', '-- 图片存储路径: E:\\ _Image_Hosting\\uploads\\genshin-impact\\', '']
matched = 0
unmatched = []

for abbr in sorted(chars.keys()):
    cname = chars[abbr]
    icon_key = mapping.get(cname)
    if icon_key:
        lines.append(f"UPDATE characters SET avatar_url = ARRAY['/images/genshin-impact/{icon_key}.png', '']::text[] WHERE abbr = '{abbr}';")
        matched += 1
    else:
        unmatched.append(cname)

lines.append('')
lines.append(f'-- 匹配成功: {matched}')
lines.append(f'-- 匹配失败: {len(unmatched)}')
for n in unmatched:
    lines.append(f'--   {n}')

outpath = os.path.join(DB_DIR, 'update_avatar_url.sql')
with open(outpath, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print(f'Generated: {outpath}')
print(f'Matched: {matched}, Unmatched: {len(unmatched)}')
if unmatched:
    print(f'Unmatched: {unmatched}')
