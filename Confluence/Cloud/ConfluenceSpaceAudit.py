import requests
import csv
from datetime import datetime
from urllib.parse import urljoin

# ========= USER CONFIGURATION =========
user = ""
token = ""
baseurl = ""
output_csv = ""
unknown = ""
# ======================================

baseurl = baseurl.rstrip('/')
AUTH = (user, token)
HEADERS = {"Accept": "application/json"}
user_cache = {}
page_limit = 250  # Set how many results per page, still fetches all with pagination

def format_date(date_str):
    if date_str:
        try:
            dt = datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")
            return dt.strftime("%d-%m-%Y")
        except ValueError:
            pass
    return unknown

def get_user_info(account_id):
    if not account_id:
        return (unknown, unknown)
    if account_id in user_cache:
        return user_cache[account_id]

    url = f"{baseurl}/rest/api/2/user?accountId={account_id}"
    response = requests.get(url, headers=HEADERS, auth=AUTH)

    if response.status_code == 200:
        user_data = response.json()
        email = user_data.get("emailAddress")
        display_name = user_data.get("displayName", "")
        active = user_data.get("active", None)

        name = email if email else display_name if display_name else unknown
        status = "Active" if active is True else "Inactive" if active is False else unknown

        result = (name, status)
        user_cache[account_id] = result
        return result

    # Fallback on failure
    user_cache[account_id] = (unknown, unknown)
    return (unknown, unknown)

def get_space_pages(space_id):
    pages = []
    url = f"{baseurl}/wiki/api/v2/spaces/{space_id}/pages?limit={page_limit}"
    while url:
        response = requests.get(url, headers=HEADERS, auth=AUTH)
        if response.status_code != 200:
            break
        data = response.json()
        pages.extend(data.get("results", []))
        next_link = data.get("_links", {}).get("next")
        url = urljoin(f"{baseurl}/wiki/", next_link) if next_link else None
    return pages

def get_space_size(space_id):
    pages = get_space_pages(space_id)
    total_size_bytes = 0
    for page in pages:
        url = f"{baseurl}/wiki/api/v2/pages/{page['id']}/attachments?limit={page_limit}"
        while url:
            resp = requests.get(url, headers=HEADERS, auth=AUTH)
            if resp.status_code != 200:
                break
            data = resp.json()
            for attachment in data.get("results", []):
                total_size_bytes += int(attachment.get("fileSize", 0))
            next_link = data.get("_links", {}).get("next")
            url = urljoin(f"{baseurl}/wiki/", next_link) if next_link else None
    return round(total_size_bytes / (1024 ** 3), 2)  # GB

def get_last_modified_info(space_key):
    cql = f"space={space_key} and type=page order by lastmodified desc"
    url = f"{baseurl}/wiki/rest/api/content/search?cql={cql}&expand=version&limit=1"
    response = requests.get(url, headers=HEADERS, auth=AUTH)
    if response.status_code != 200:
        return unknown, unknown, unknown
    data = response.json()
    results = data.get("results", [])
    if not results:
        return unknown, unknown, unknown
    version = results[0].get("version", {})
    when = version.get("when")
    lastmod_date = format_date(when)
    modifier_info = version.get("by", {})
    account_id = modifier_info.get("accountId")
    last_modifier, modifier_status = get_user_info(account_id)
    return lastmod_date, last_modifier, modifier_status

def get_all_spaces():
    spaces = []
    url = f"{baseurl}/wiki/api/v2/spaces?limit={page_limit}"
    while url:
        response = requests.get(url, headers=HEADERS, auth=AUTH)
        if response.status_code != 200:
            print(f"❌ Failed to fetch spaces: {response.text}")
            break
        data = response.json()
        spaces.extend(data.get("results", []))
        next_link = data.get("_links", {}).get("next")
        url = urljoin(f"{baseurl}/wiki/", next_link) if next_link else None
    return spaces

def extract_confluence_metadata():
    print("🔍 Starting metadata extraction...")
    print(f"👤 User: {user}")
    print(f"🔗 Base URL: {baseurl}")
    print(f"📁 Output File: {output_csv}")
    print("======================================\n")

    spaces = get_all_spaces()
    total_spaces = len(spaces)
    print(f"📦 Total spaces found: {total_spaces}\n")

    with open(output_csv, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "Space ID", "Space Key", "Space Name", "Type", "Status",
            "Creator", "Creator Status", "Last Modifier", "Modifier Status",
            "Created Date", "Last Modified Date", "Number of Pages", "Space Size (GB)", "URL"
        ])

        for idx, space in enumerate(spaces, start=1):
            space_id = space.get("id", unknown)
            key = space.get("key", unknown)
            name = space.get("name", unknown)
            type_ = space.get("type", unknown)
            status = space.get("status", unknown)

            creator_id = space.get("authorId", "")
            creator_name, creator_status = get_user_info(creator_id)

            created_date = format_date(space.get("createdAt"))
            lastmod_date, last_modifier, modifier_status = get_last_modified_info(key)

            pages = get_space_pages(space_id)
            page_count = len(pages)
            space_size_gb = get_space_size(space_id)

            url = f"{baseurl}/wiki/spaces/{key}/overview"

            writer.writerow([
                space_id, key, name, type_, status,
                creator_name, creator_status, last_modifier, modifier_status,
                created_date, lastmod_date, page_count, space_size_gb, url
            ])
            print(f"✅ [{idx}/{total_spaces}] Processed: {key} - {name}")

    print("\n✅ Done. Output written to:", output_csv)

# Run the script
extract_confluence_metadata()
