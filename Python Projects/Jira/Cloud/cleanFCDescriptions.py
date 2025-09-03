import requests
from requests.auth import HTTPBasicAuth
import re
import json
import time
import csv
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# ⚙️ CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
email = 'your_email@example.com'
token = 'your_api_token'
baseurl = 'https://yourdomain.atlassian.net'
log_file = 'log_clean_cf.csv'
page_size = 50  # Do not modify this value over 50
dryRun = True  # True = simulate only, False = apply changes
# ─────────────────────────────────────────────────────────────────────────────

baseurl = baseurl.rstrip('/')
auth = HTTPBasicAuth(email, token)
headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

start_time = time.time()

with open(log_file, mode='w', newline='', encoding='utf-8') as logfile:
    writer = csv.writer(logfile)
    writer.writerow(['Time', 'Field Configuration ID', 'CF ID', 'Code', 'Message'])

    # Get all field configurations
    fc_response = requests.get(f"{baseurl}/rest/api/3/fieldconfiguration", headers=headers, auth=auth)
    fc_data = fc_response.json()
    total_fcs = fc_data.get('total', 0)

    print(f"🔧 Total field configurations: {total_fcs}")

    for fc_index, fc in enumerate(fc_data.get('values', []), start=1):
        fc_id = fc['id']
        print(f"\n🔍 Processing configuration [{fc_index}/{total_fcs}] ID: {fc_id}")

        start_at = 0
        processed = 0

        while True:
            params = {
                'startAt': start_at,
                'maxResults': page_size
            }
            cf_response = requests.get(
                f"{baseurl}/rest/api/3/fieldconfiguration/{fc_id}/fields",
                headers=headers,
                auth=auth,
                params=params
            )

            if cf_response.status_code != 200:
                print(f"❌ Failed to get fields for FC {fc_id}: {cf_response.status_code}")
                break

            cf_data = cf_response.json()
            fields = cf_data.get("values", [])
            total_fields = cf_data.get("total", 0)

            if not fields:
                break

            for field in fields:
                processed += 1
                cf_id = field.get('id')
                cf_desc = field.get('description', '')

                cleaned_desc = re.sub(r'\(Migrated on .*\)$', '', cf_desc).strip()

                payload = json.dumps({
                    "fieldConfigurationItems": [
                        {
                            "id": cf_id,
                            "description": cleaned_desc
                        }
                    ]
                })

                if dryRun:
                    status_code = 'DRY'
                    message = 'Dry run - not updated'
                else:
                    put_response = requests.put(
                        f"{baseurl}/rest/api/3/fieldconfiguration/{fc_id}/fields",
                        headers=headers,
                        auth=auth,
                        data=payload
                    )
                    status_code = put_response.status_code
                    if status_code in [200, 201, 204]:
                        message = 'Successful'
                    else:
                        try:
                            message = put_response.json().get('errorMessages', ['Unknown error'])[0]
                        except Exception:
                            message = 'Unparseable error'

                print(f"[{processed}/{total_fields}] FC {fc_id} | CF {cf_id} | {status_code} - {message}")
                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    fc_id,
                    cf_id,
                    status_code,
                    message
                ])

            start_at += page_size
            if start_at >= total_fields:
                break

elapsed = round(time.time() - start_time, 2)
print(f"\n✅ Completed in {elapsed} seconds")
print(f"📄 Log saved to: {log_file}")
