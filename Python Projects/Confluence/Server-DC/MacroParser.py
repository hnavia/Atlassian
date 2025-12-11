import csv
import re
import os

# === Input file ===
input_file = r'C:\Users\hugon\Desktop\Tools\Standalone Apps\Confluence\macros.txt'

# === Output file ===
base, _ = os.path.splitext(input_file)
output_file = f'{base}_list.csv'

# === Regular expressions ===
macro_pattern = re.compile(r'^([a-zA-Z0-9\-_]+)\s*\(\s*(\d+)\s*\)$')
number_pattern = re.compile(r'^\d+$')

# === Read file safely ===
try:
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines()]
except FileNotFoundError:
    print(f"❌ ERROR: File not found: {input_file}")
    raise
except Exception as e:
    print(f"❌ ERROR reading file: {e}")
    raise

# === Detect type (Cloud vs DC) ===
non_empty = [L for L in lines if L]
macro_lines = [L for L in non_empty if "(" in L]

is_cloud = any("(" in L and ")" in L and " " not in L for L in macro_lines)

print(f"🔍 Auto-detected format: {'CLOUD' if is_cloud else 'DATA CENTER'}")

plugin_name = None
rows = []
seen = set()

# === Parsing loop ===
for line in lines:
    if not line:
        continue

    if number_pattern.match(line):
        continue  # skip total numbers

    # Plugin detection
    if "(" not in line:
        clean_name = re.sub(r'\b[Pp]lugin\b', '', line).strip()
        plugin_name = clean_name
        continue

    # Macro detection
    match = macro_pattern.match(line)
    if not match:
        print(f"⚠️ Warning: Ignored malformed macro line: '{line}'")
        continue

    if not plugin_name:
        print(f"⚠️ Warning: Macro found before plugin name: '{line}'")
        continue

    macro_name, macro_count = match.groups()

    pair = (plugin_name, macro_name)
    if pair not in seen:
        rows.append((plugin_name, macro_name, macro_count))
        seen.add(pair)

# === Validate results ===
if not rows:
    print("❌ ERROR: No macros detected. Check file format or content.")
    raise SystemExit

# === Write CSV ===
try:
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Plugin Name', 'Macro Name', 'Macro Count'])
        writer.writerows(rows)
except Exception as e:
    print(f"❌ ERROR saving CSV: {e}")
    raise

print(f"✅ File successfully generated: {output_file}")
print(f"📊 Total macros processed: {len(rows)}")
