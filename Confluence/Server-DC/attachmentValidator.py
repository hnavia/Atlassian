import csv
import time
import asyncio
import aiohttp
import aiofiles
import io
from urllib.parse import quote

# ==================== CONFIGURATION ====================
auth_type = "PAT"  # Options: "PAT" or "Basic"
pat = ''
userName = ''
password = ''
baseurl = ''
input_csv_file = r''
output_csv_file = input_csv_file.replace('.csv', '_errors_all.csv')
column_indexes = {
    "contentid": 0,
    "spacename": 1,
    "spacekey": 2,
    "pageid": 3,
    "file_name": 4
}
concurrent_requests = 20  # Limit of concurrent connections
save_all = True  # True = Save all rows including successful ones | False = Save only the error results
# =======================================================

baseurl = baseurl.rstrip('/')
headers = {'Accept': 'application/json'}
if auth_type == "PAT":
    headers['Authorization'] = f"Bearer {pat}"

def encode_filename(filename):
    return quote(filename, safe='')

def build_download_url(pageid, filename):
    return f"{baseurl}/download/attachments/{pageid}/{encode_filename(filename)}?api=v2"

def build_api_url(pageid, filename):
    return f"{baseurl}/rest/api/content/{pageid}/child/attachment?filename={encode_filename(filename)}"

async def check_attachment(session, semaphore, row, index, total):
    pageid = row[column_indexes["pageid"]]
    raw_filename = row[column_indexes["file_name"]]

    download_url = build_download_url(pageid, raw_filename)
    api_url = build_api_url(pageid, raw_filename)

    row.insert(5, download_url)  # Insert the generated download URL at index 5
    row.insert(6, api_url)       # Insert the generated API URL at index 6

    async with semaphore:
        try:
            async with session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    found = any(att.get("title", "").lower() == raw_filename.lower() for att in data.get("results", []))
                    if not found:
                        raise ValueError("Attachment not found in results")
                    print(f"[ {index} / {total} ] {row[column_indexes['spacename']]} - {row[column_indexes['spacekey']]} - {raw_filename} - 200 - OK")
                    if save_all:
                        return row + ["", ""]
                else:
                    text = await response.text()
                    raise Exception(f"HTTP {response.status}: {text}")

        except Exception as e:
            err_code = getattr(e, 'status', 'N/A')
            err_msg = str(e)
            print(f"[ {index} / {total} ] {row[column_indexes['spacename']]} - {row[column_indexes['spacekey']]} - {raw_filename} - {err_code} - {err_msg}")
            return row + [err_code, err_msg]

    return None

async def main():
    start_time = time.time()
    print("🔍 Starting attachment validation...")

    connector = aiohttp.TCPConnector(limit=concurrent_requests)
    async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
        tasks = []
        semaphore = asyncio.Semaphore(concurrent_requests)

        async with aiofiles.open(input_csv_file, mode='r', encoding='utf-8') as f:
            reader = await f.read()
            lines = list(csv.reader(reader.splitlines()))

        total = len(lines) - 1  # exclude header
        header = lines[0]
        header.insert(5, 'download_url')  # Add download_url header at index 5
        header.insert(6, 'rest_api_url')  # Add API URL header at index 6
        header += ['error_code', 'error_message']

        for idx, row in enumerate(lines[1:], start=1):
            task = check_attachment(session, semaphore, row, idx, total)
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        final_rows = [r for r in results if r] if not save_all else results

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(header)
        writer.writerows(final_rows)

        async with aiofiles.open(output_csv_file, mode='w', encoding='utf-8', newline='') as f:
            await f.write(buffer.getvalue())

        elapsed = round(time.time() - start_time, 2)
        print(f"\n✅ Validation completed in {elapsed} seconds. Output saved to: {output_csv_file}")

if __name__ == '__main__':
    asyncio.run(main())
