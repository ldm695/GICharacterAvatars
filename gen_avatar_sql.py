import json, re

with open(r'D:\Projects\CustomProjects\GINoteMax\gi_character_icons\character_icon_mapping.json', encoding='utf-8') as f:
    mapping = json.load(f)

seedpath = r'D:\Projects\CustomProjects\GINoteMax\gi-note-server\src\main\resources\db\seed.sql'
pattern = re.compile(r"INSERT INTO characters \(id, name, abbr, rarity, release_date, status\) VALUES \((\d+), '([^']+)', '([^']+)',")

names = {}
with open(seedpath, encoding='utf-8') as f:
    for line in f:
        m = pattern.search(line)
        if m:
            names[int(m.group(1))] = m.group(2)

lines = ['-- avatar_url 写入脚本', '-- 图片存储路径: E:\\ _Image_Hosting\\uploads\\genshin-impact\\', '']
matched = 0
unmatched = []

for cid in sorted(names.keys()):
    cname = names[cid]
    icon_key = mapping.get(cname)
    if icon_key:
        lines.append(f"UPDATE characters SET avatar_url = ARRAY['/images/genshin-impact/{icon_key}.png', '']::text[] WHERE id = {cid};")
        matched += 1
    else:
        unmatched.append(cname)

lines.append('')
lines.append(f'-- 匹配成功: {matched}')
lines.append(f'-- 匹配失败: {len(unmatched)}')
for n in unmatched:
    lines.append(f'--   {n}')

outpath = r'D:\Projects\CustomProjects\GINoteMax\gi-note-server\src\main\resources\db\update_avatar_url.sql'
with open(outpath, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print(f'Generated: {outpath}')
print(f'Matched: {matched}, Unmatched: {len(unmatched)}')
if unmatched:
    print(f'Unmatched: {unmatched}')
