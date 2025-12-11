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
email = ''
token = ''
baseurl = ''
log_file = ''
page_size = 50  # Do not modify this value over 50
dryRun = False  # True = simulate only, False = apply changes
wait_seconds = 600  # 10 minutes = 600 seconds
# ─────────────────────────────────────────────────────────────────────────────

baseurl = baseurl.rstrip('/')
auth = HTTPBasicAuth(email, token)
headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}
DEFAULT_TIMEOUT = (10, 60)  # (connect timeout, read timeout)

# ─────────────────────────────────────────────────────────────────────────────
# 🔁 Retry Helper with 429 & Connection Error Handling
# ─────────────────────────────────────────────────────────────────────────────
def send_request_with_retries(method, url, **kwargs):
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.request(method, url, timeout=DEFAULT_TIMEOUT, **kwargs)
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Request error on attempt {attempt}: {e}")
            if attempt < max_retries:
                time.sleep(10)
                continue
            else:
                print("❌ Max retries exceeded due to connection errors.")
                return None

        if response.status_code != 429:
            return response

        retry_after = int(response.headers.get('Retry-After', '60'))
        print(f"⚠️ 429 Too Many Requests. Waiting {retry_after} seconds before retry {attempt}/{max_retries}...")
        time.sleep(retry_after)

    print("❌ Max retries exceeded.")
    return response

# ─────────────────────────────────────────────────────────────────────────────
# 🛠️ Main Logic
# ─────────────────────────────────────────────────────────────────────────────
start_time = time.time()
updated_fc_ids = set()

with open(log_file, mode='w', newline='', encoding='utf-8') as logfile:
    writer = csv.writer(logfile)
    writer.writerow(['Time', 'Field Configuration ID', 'CF ID', 'Code', 'Message'])

    start_at_fc = 0
    fc_index = 0
    total_fcs = None

    while True:
        params = {
            'startAt': start_at_fc,
            'maxResults': page_size
        }

        fc_response = send_request_with_retries(
            "GET", f"{baseurl}/rest/api/3/fieldconfiguration",
            headers=headers, auth=auth, params=params
        )

        if fc_response is None:
            print("❌ Could not retrieve field configurations. Exiting.")
            exit(1)

        fc_data = fc_response.json()
        fcs = fc_data.get('values', [])
        total_fcs = fc_data.get('total', 0)

        if not fcs:
            break

        for fc in fcs:
            fc_index += 1
            fc_id = fc['id']
            print(f"\n🔍 Processing configuration [{fc_index}/{total_fcs}] ID: {fc_id}")

            start_at = 0
            processed = 0

            while True:
                params = {
                    'startAt': start_at,
                    'maxResults': page_size
                }

                cf_response = send_request_with_retries(
                    "GET", f"{baseurl}/rest/api/3/fieldconfiguration/{fc_id}/fields",
                    headers=headers,
                    auth=auth,
                    params=params
                )

                if cf_response is None or cf_response.status_code != 200:
                    print(f"❌ Failed to get fields for FC {fc_id}: {getattr(cf_response, 'status_code', 'No response')}")
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
                        put_response = send_request_with_retries(
                            "PUT", f"{baseurl}/rest/api/3/fieldconfiguration/{fc_id}/fields",
                            headers=headers,
                            auth=auth,
                            data=payload
                        )
                        if put_response is None:
                            status_code = 'ERR'
                            message = 'Connection failed'
                        else:
                            status_code = put_response.status_code
                            if status_code in [200, 201, 204]:
                                message = 'Successful'
                                updated_fc_ids.add(fc_id)
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

            # Wait 10 minutes between field configurations
            print(f"\n⏳ Waiting {wait_seconds // 60} minutes to avoid rate limits...")
            for remaining in range(wait_seconds, 0, -10):
                print(f"   🔄 Resuming in {remaining} seconds...", end='\r')
                time.sleep(10)
            print("   ✅ Continuing...\n")

        start_at_fc += page_size
        if start_at_fc >= total_fcs:
            break

elapsed = round(time.time() - start_time, 2)
print(f"\n✅ Completed in {elapsed} seconds")
print(f"🧾 Field configurations changed: {len(updated_fc_ids)}")
print(f"📄 Log saved to: {log_file}")