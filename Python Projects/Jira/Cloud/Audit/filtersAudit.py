import csv
import requests
from requests.auth import HTTPBasicAuth
import time
import json
from collections import defaultdict

# ========= CONFIGURATION =========
# IMPORTANT: Replace these values with your actual credentials and settings.
user = 'email'
token = 'TOKEN'
baseurl = 'https://{instance}.atlassian.net/'  # Enter the base URL of the Cloud site
csv_file = r'C:\path\to\file\filter_audit.csv'  # Enter the path and name of the output csv path
page_size = 50  # Max allowed by Jira is 50 for most endpoints
# =================================

# --- Session Setup ---
baseurl = baseurl.rstrip('/')
auth = HTTPBasicAuth(user, token)
headers = {'Accept': 'application/json'}
session = requests.Session()
session.auth = auth
session.headers.update(headers)

# --- Caching ---
screen_to_fields_cache = {}
issue_type_name_cache = {}
screen_scheme_cache = {}
user_details_cache = {}  # Cache for user details to avoid redundant API calls


# === HELPER FUNCTIONS ===

def make_request(url):
    """
    Makes a request to the API and handles common errors.
    Returns the JSON response or None if an error occurs.
    """
    try:
        response = session.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        # Ignore 404 Not Found, as some properties may not exist
        if e.response.status_code == 404:
            return None
        print(f"HTTP Error for {url}: {e.response.status_code} {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed for {url}: {e}")
        return None


def get_paginated_data(url, key='values'):
    """
    Fetches all results from a paginated API endpoint.
    Handles different pagination styles (isLast vs. total).
    """
    results = []
    start_at = 0
    while True:
        paginated_url = f"{url}{'&' if '?' in url else '?'}startAt={start_at}&maxResults={page_size}"
        data = make_request(paginated_url)

        if not data:
            break

        page_values = data.get(key)

        # If the key is not found, check if the entire response is the list
        if page_values is None and isinstance(data, list):
            page_values = data

        if not page_values:
            break

        results.extend(page_values)

        # --- PAGINATION LOGIC CORRECTION ---
        # Handle endpoints that use 'isLast' (e.g., Agile boards, filters)
        if 'isLast' in data:
            if data['isLast']:
                break
        # Handle endpoints that use 'total' (e.g., dashboards)
        else:
            total = data.get('total', 0)
            if (start_at + len(page_values)) >= total:
                break

        # Safety break if we received an empty page
        if not page_values:
            break

        start_at += len(page_values)

    return results


def get_user_details(account_id):
    """
    Fetches details for a specific user and caches the result.
    """
    if not account_id or account_id in user_details_cache:
        return user_details_cache.get(account_id)

    print(f"   - Fetching details for user: {account_id}")
    url = f"{baseurl}/rest/api/3/user/search?accountId={account_id}"
    user_data = make_request(url)

    # The endpoint returns a list, we need the first element
    if user_data and isinstance(user_data, list):
        details = user_data[0]
        user_details_cache[account_id] = {
            'emailAddress': details.get('emailAddress', 'N/A'),
            'active': details.get('active', False)
        }
        return user_details_cache[account_id]

    # Cache the negative result to avoid re-fetching
    user_details_cache[account_id] = None
    return None


def get_all_filters():
    """Fetches all filters in the Jira instance."""
    print("Fetching all filters...")
    # expand=owner is still useful to get the accountId without an extra call
    url = f"{baseurl}/rest/api/3/filter/search?expand=owner,jql,sharePermissions&overrideSharePermissions=True"
    filters = get_paginated_data(url)
    print(f" - Found {len(filters)} filters.")
    return filters


def get_all_boards():
    """Fetches all boards and their associated filter IDs."""
    print("Fetching all boards...")
    url = f"{baseurl}/rest/agile/1.0/board"
    boards = get_paginated_data(url)
    board_to_filter_map = defaultdict(list)
    total_boards = len(boards)

    for i, board in enumerate(boards, 1):
        # Progress indicator
        print(f" - Analyzing board {i}/{total_boards}: {board['name']}")
        config_url = f"{baseurl}/rest/agile/1.0/board/{board['id']}/configuration"
        config_data = make_request(config_url)
        if config_data:
            filter_id = config_data.get('filter', {}).get('id')
            if filter_id:
                board_to_filter_map[str(filter_id)].append({
                    'board_id': board['id'],
                    'board_name': board['name']
                })
    print(f" - Found {len(board_to_filter_map)} unique filters used in boards.")
    return board_to_filter_map


def get_dashboard_gadgets():
    """
    Fetches all dashboards and finds gadgets that use a filter.
    """
    print("Fetching all dashboards and gadgets...")
    dashboard_url = f"{baseurl}/rest/api/3/dashboard"
    dashboards = get_paginated_data(dashboard_url, key='dashboards')
    filter_to_dashboards = defaultdict(list)
    total_dashboards = len(dashboards)

    for i, dashboard in enumerate(dashboards, 1):
        # Progress indicator
        print(f" - Analyzing dashboard {i}/{total_dashboards}: {dashboard['name']}")
        gadget_url = f"{baseurl}/rest/api/3/dashboard/{dashboard['id']}/gadget"
        gadgets = get_paginated_data(gadget_url, key='gadgets')

        for gadget in gadgets:
            gadget_id = gadget.get('id')
            if not gadget_id: continue

            properties_url = f"{baseurl}/rest/api/3/dashboard/{dashboard['id']}/items/{gadget_id}/properties/config"
            properties_data = make_request(properties_url)

            if properties_data:
                config_value = properties_data.get('value', {})
                if isinstance(config_value, str):
                    try:
                        config_value = json.loads(config_value)
                    except json.JSONDecodeError:
                        continue

                if isinstance(config_value, dict):
                    raw_filter_id = config_value.get('filterId')
                    if raw_filter_id and isinstance(raw_filter_id, str):
                        filter_id = raw_filter_id.replace('filter-', '')
                        if filter_id.isdigit():
                            filter_to_dashboards[filter_id].append(str(dashboard['id']))

    print(f" - Found {len(filter_to_dashboards)} unique filters used in dashboards.")
    return filter_to_dashboards


# === MAIN LOGIC ===
start_time = time.time()

# 1. Fetch all necessary data from Jira
all_filters = get_all_filters()
board_usage = get_all_boards()
dashboard_usage = get_dashboard_gadgets()

# 2. Process and aggregate the data
final_results = []
total_filters = len(all_filters)
print(f"\nProcessing and aggregating data for {total_filters} filters...")
for i, f in enumerate(all_filters, 1):
    print(f" - Processing filter {i}/{total_filters}: {f.get('name', 'N/A')}")
    filter_id_str = str(f['id'])

    # Determine usage
    boards = board_usage.get(filter_id_str, [])
    dashboards = dashboard_usage.get(filter_id_str, [])

    used_in_parts = []
    if boards: used_in_parts.append('Board')
    if dashboards: used_in_parts.append('Dashboard')

    # Get enriched user details
    owner_info = f.get('owner', {})
    account_id = owner_info.get('accountId')
    user_details = get_user_details(account_id)

    owner_email = user_details.get('emailAddress', 'N/A') if user_details else 'N/A (User Deleted or Private)'
    owner_status_bool = user_details.get('active', False) if user_details else False

    shared_projects = [p.get('project', {}).get('key') for p in f.get('sharePermissions', []) if p.get('type') == 'project']

    final_results.append({
        'filter_id': filter_id_str,
        'filtername': f.get('name', 'N/A'),
        'user_id': account_id or 'N/A',
        'owner': owner_email,
        'owner_status': 'Active' if owner_status_bool else 'Inactive',
        'project_key': ', '.join(filter(None, shared_projects)),
        'board_ids': ', '.join(str(b['board_id']) for b in boards),
        'board_name': ', '.join(b['board_name'] for b in boards),
        'dashboard_id': ', '.join(sorted(list(set(dashboards)))),
        'used_in': ', '.join(used_in_parts),
        'jql': f.get('jql', '').replace('\r', ' ').replace('\n', ' ')
    })

# 3. Write to CSV
print(f"\nWriting {len(final_results)} rows to {csv_file}...")
if final_results:
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=final_results[0].keys())
        writer.writeheader()
        writer.writerows(final_results)

end_time = time.time()
print(f"\nDone. Script finished in {end_time - start_time:.2f} seconds.")
