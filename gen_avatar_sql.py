import json
import re
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# The main project server sits alongside character-avatars, under GINote/
DB_DIR = os.path.normpath(
    os.path.join(BASE_DIR, '..', 'gi-note-server', 'src', 'main', 'resources', 'db')
)

with open(os.path.join(BASE_DIR, 'avatar_mapping.json'), encoding='utf-8') as f:
    mapping = json.load(f)

seed_path = os.path.join(DB_DIR, 'seed.sql')
if not os.path.isfile(seed_path):
    raise SystemExit(
        f'seed.sql not found: {seed_path}\n'
        f'Please confirm the main project path (GINote/gi-note-server).'
    )
# After the UUID migration, id is md5('character:ABBR')::uuid, no longer an integer.
# Use abbr as the lookup key (id in seed is itself derived from abbr); name is used
# for the mapping lookup.
pattern = re.compile(
    r"INSERT INTO characters \(id, name, abbr, rarity, release_date, status\) VALUES "
    r"\([^,]+, '([^']+)', '([^']+)',"
)

# abbr -> name
chars = {}
with open(seed_path, encoding='utf-8') as f:
    for line in f:
        m = pattern.search(line)
        if m:
            chars[m.group(2)] = m.group(1)

lines = [
    '-- avatar_url update script',
    '-- Image storage path: E:\\ _Image_Hosting\\uploads\\genshin-impact\\',
    '',
]
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
lines.append(f'-- Matched: {matched}')
lines.append(f'-- Unmatched: {len(unmatched)}')
for n in unmatched:
    lines.append(f'--   {n}')

output_path = os.path.join(DB_DIR, 'update_avatar_url.sql')
with open(output_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print(f'Generated: {output_path}')
print(f'Matched: {matched}, Unmatched: {len(unmatched)}')
if unmatched:
    print(f'Unmatched: {unmatched}')
