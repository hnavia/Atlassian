import requests
from requests.auth import HTTPBasicAuth
import json
import re
from datetime import datetime
import time
import csv

# ─────────────────────────────────────────────────────────────────────────────
# ⚙️ CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
email = 'your_email@example.com'
token = 'your_api_token'
base_url = 'https://yourdomain.atlassian.net'
log_file = 'log_clean_cf.csv'
page_size = 50  # Do not modify this value over 50
dryRun = True  # True = simulate only, False = apply changes
# ─────────────────────────────────────────────────────────────────────────────

base_url = base_url.rstrip('/')
auth = HTTPBasicAuth(email, token)
headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

start_time = time.time()

# 📝 Prepare log file
with open(log_file, mode='w', newline='', encoding='utf-8') as logfile:
    writer = csv.writer(logfile)
    writer.writerow(['Time', 'Field ID', 'Field Name', 'Code', 'Message'])

    print("📦 Retrieving custom fields...")

    # 🔄 Initial fetch to get total fields
    init_resp = requests.get(f"{base_url}/rest/api/3/field/search", headers=headers, auth=auth)
    if init_resp.status_code != 200:
        print(f"❌ Error fetching fields: {init_resp.status_code}")
        exit(1)

    total = init_resp.json().get("total", 0)
    print(f"🔢 Total custom fields found: {total}\n")

    start_at = 0
    processed = 0

    # 🔁 Batch processing
    while start_at < total:
        params = {
            'startAt': start_at,
            'maxResults': page_size
        }
        response = requests.get(f"{base_url}/rest/api/3/field/search", headers=headers, auth=auth, params=params)

        if response.status_code != 200:
            print(f"❌ Failed to fetch batch starting at {start_at}: {response.status_code}")
            break

        fields = response.json().get("values", [])
        for field in fields:
            processed += 1
            cf_id = field.get('id')
            cf_name = field.get('name', '')
            cf_desc = field.get('description', '')

            # 🧽 Clean name and description
            clean_name = re.sub(r'\(migrated.*\)$', '', cf_name).strip()
            clean_desc = re.sub(r'\(Migrated on .*\)$', '', cf_desc).strip()

            payload_data = {'name': clean_name}
            if cf_desc:
                payload_data['description'] = clean_desc

            payload = json.dumps(payload_data)

            # Si dryRun está activo, no hacemos PUT, solo simulamos
            if dryRun:
                status_code = 'DRY-RUN'
                message = 'Simulated - No changes applied'
            else:
                put_url = f"{base_url}/rest/api/3/field/{cf_id}"
                put_resp = requests.put(put_url, headers=headers, auth=auth, data=payload)
                status_code = put_resp.status_code
                if status_code in [200, 204]:
                    message = 'Successful'
                else:
                    try:
                        message = put_resp.json().get("errorMessages", ["Unknown error"])[0]
                    except Exception:
                        message = "Unparseable error"

            print(f"[{str(processed).rjust(len(str(total)))} / {total}] {clean_name} - {status_code} - {message}")
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                cf_id,
                clean_name,
                status_code,
                message
            ])

        start_at += page_size

# ✅ Done
duration = round(time.time() - start_time, 2)
print(f"\n✅ Completed: {processed} fields in {duration} seconds")
print(f"📄 Log saved to: {log_file}")
