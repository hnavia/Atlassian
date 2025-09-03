import requests
from requests.auth import HTTPBasicAuth
import csv
from collections import defaultdict
import time
import json

# === CONFIGURATION ===
# IMPORTANT: Replace these values with your credentials.
user = ''
token = ''
baseurl = ''

# Set to True to audit all projects, or False to use the list below.
allProjects = True
project_keys = ['PROJ1', 'PROJ2']  # Only used if allProjects = False.

output_file = r''

# === SESSION SETUP ===
baseurl = baseurl.rstrip('/')
s = requests.Session()
s.auth = HTTPBasicAuth(user, token)
s.headers.update({
    'Accept': 'application/json',
    'Content-Type': 'application/json'
})

# --- Caching ---
screen_to_fields_cache = {}
issue_type_name_cache = {}
screen_scheme_cache = {}


# === HELPER FUNCTIONS ===
def handle_rate_limit(resp):
    """Simple handler for API rate limiting."""
    if resp.status_code == 429:
        retry_after = int(resp.headers.get("Retry-After", 30))
        print(f"[WARNING] Rate limit reached. Retrying in {retry_after} seconds...")
        time.sleep(retry_after)
        return True
    return False


def make_request(url):
    """Makes a request to the API, handling retries and common errors."""
    while True:
        try:
            resp = s.get(url)
            if handle_rate_limit(resp):
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            print(f"[ERROR] HTTP Error for {url}: {e.response.status_code} {e.response.text}")
            return None
        except json.JSONDecodeError as e:
            print(f"[ERROR] Could not decode JSON response from {url}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Request to {url} failed: {e}")
            return None


def get_paginated_data(url):
    """Gets all results from a paginated API endpoint."""
    results = []
    start_at = 0
    while True:
        paginated_url = f"{url}{'&' if '?' in url else '?'}startAt={start_at}&maxResults=50"
        data = make_request(paginated_url)
        if not data or 'values' not in data:
            break

        page_values = data.get('values', [])
        results.extend(page_values)

        if data.get('isLast', True):
            break
        start_at += len(page_values)
    return results


def get_all_projects():
    print("Fetching all projects...")
    projects = get_paginated_data(f"{baseurl}/rest/api/3/project/search")
    print(f" - Found {len(projects)} projects.")
    return [{'key': p['key'], 'id': p['id']} for p in projects]


def get_all_custom_fields():
    print("Fetching all custom fields...")
    fields = make_request(f"{baseurl}/rest/api/3/field")
    if not fields:
        return {}
    custom_fields = {f['id']: f['name'] for f in fields if f.get('custom', False)}
    print(f" - Found {len(custom_fields)} custom fields.")
    return custom_fields


def get_all_issue_types():
    """Gets all issue types to display their names."""
    print("Fetching all issue types for reference...")
    issue_types = make_request(f"{baseurl}/rest/api/3/issuetype")
    if issue_types:
        for it in issue_types:
            issue_type_name_cache[it['id']] = it['name']
    print(f" - Cached {len(issue_type_name_cache)} issue type names.")


def get_all_screen_schemes():
    """Gets all screen schemes and stores them in cache."""
    print("Fetching all screen schemes...")
    schemes = get_paginated_data(f"{baseurl}/rest/api/3/screenscheme")
    for scheme in schemes:
        screen_scheme_cache[str(scheme['id'])] = scheme
    print(f" - Cached {len(screen_scheme_cache)} screen schemes.")


def get_fields_for_screen(screen_id):
    """Gets all fields for a screen, using the cache for efficiency."""
    if screen_id in screen_to_fields_cache:
        return screen_to_fields_cache[screen_id]

    print(f"  - Analyzing Screen ID: {screen_id}")
    tabs_url = f"{baseurl}/rest/api/3/screens/{screen_id}/tabs"
    tabs = make_request(tabs_url)
    if not tabs:
        screen_to_fields_cache[screen_id] = {'fields': [], 'name': f"Screen {screen_id}"}
        return screen_to_fields_cache[screen_id]

    all_fields = []
    screen_name = f"Screen {screen_id}"
    if tabs:
        screen_name = tabs[0].get('name', screen_name)

    for tab in tabs:
        fields_url = f"{baseurl}/rest/api/3/screens/{screen_id}/tabs/{tab['id']}/fields"
        fields_on_tab = make_request(fields_url)
        if fields_on_tab:
            all_fields.extend(fields_on_tab)

    screen_to_fields_cache[screen_id] = {'fields': all_fields, 'name': screen_name}
    return screen_to_fields_cache[screen_id]


# === MAIN LOGIC ===
start_time = time.time()

# Initial data load
custom_field_map = get_all_custom_fields()
get_all_issue_types()
get_all_screen_schemes()
if allProjects:
    projects_to_scan = get_all_projects()
else:
    print(f"Fetching details for specific projects: {project_keys}")
    all_known_projects = get_all_projects()
    projects_to_scan = [p for p in all_known_projects if p['key'] in project_keys]

# List to store raw results before aggregation
raw_results = []
print("\n--- Starting Project Audit ---")

for project in projects_to_scan:
    project_key = project['key']
    project_id = project['id']
    print(f"\nProcessing project: {project_key} (ID: {project_id})")

    itss_url = f"{baseurl}/rest/api/3/issuetypescreenscheme/project?projectId={project_id}"
    itss_data = get_paginated_data(itss_url)
    if not itss_data:
        print(f" [WARNING] Project {project_key} might use a default scheme or has no direct association. Skipping.")
        continue

    issue_type_screen_scheme = itss_data[0]['issueTypeScreenScheme']
    scheme_id = issue_type_screen_scheme['id']
    scheme_name = issue_type_screen_scheme['name']
    print(f" - Found Scheme: '{scheme_name}' (ID: {scheme_id})")

    mappings_url = f"{baseurl}/rest/api/3/issuetypescreenscheme/mapping?issueTypeScreenSchemeId={scheme_id}"
    mappings = get_paginated_data(mappings_url)

    screen_scheme_to_issue_types = defaultdict(list)
    for mapping in mappings:
        issue_type_id = mapping.get('issueTypeId')
        screen_scheme_id = mapping.get('screenSchemeId')
        if screen_scheme_id:
            readable_name = issue_type_name_cache.get(issue_type_id, "Default")
            screen_scheme_to_issue_types[screen_scheme_id].append(readable_name)

    for screen_scheme_id, issue_types in screen_scheme_to_issue_types.items():
        print(f" - Analyzing Screen Scheme ID: {screen_scheme_id} (used by: {issue_types})")
        screen_scheme_details = screen_scheme_cache.get(screen_scheme_id)

        if not screen_scheme_details or 'screens' not in screen_scheme_details:
            print(f"   [WARNING] Could not get details for Screen Scheme ID: {screen_scheme_id} from cache.")
            continue

        screen_ids = set(screen_scheme_details['screens'].values())

        for screen_id in screen_ids:
            screen_data = get_fields_for_screen(screen_id)
            screen_name = screen_data['name']

            for field in screen_data['fields']:
                field_id = field.get('id')
                if field_id in custom_field_map:
                    raw_results.append({
                        'custom_field_id': field_id,
                        'custom_field_name': custom_field_map.get(field_id, 'Unknown'),
                        'screen_name': screen_name,
                        'issue_types': ', '.join(sorted(list(set(issue_types)))),
                        'scheme_name': scheme_name,
                        'project_key': project_key
                    })

# === AGGREGATION AND CSV WRITING ===
if raw_results:
    aggregated_results = {}
    print("\n--- Aggregating results for the final report ---")

    for row in raw_results:
        # The aggregation key is the field on a screen within a specific scheme.
        key = (row['custom_field_id'], row['screen_name'], row['scheme_name'])

        if key not in aggregated_results:
            aggregated_results[key] = {
                'custom_field_id': row['custom_field_id'],
                'custom_field_name': row['custom_field_name'],
                'screen_name': row['screen_name'],
                'issue_types': set(t.strip() for t in row['issue_types'].split(',')),
                'source': 'Screen Scheme',  # This source is assumed, as workflows are not analyzed.
                'scheme_name': row['scheme_name'],
                'project_keys': {row['project_key']}
            }
        else:
            # If the row already exists, update the sets of projects and issue types.
            aggregated_results[key]['project_keys'].add(row['project_key'])
            new_types = set(t.strip() for t in row['issue_types'].split(','))
            aggregated_results[key]['issue_types'].update(new_types)

    # Convert the sets to sorted, comma-separated strings.
    final_rows = []
    for data in aggregated_results.values():
        data['project_keys'] = ', '.join(sorted(data['project_keys']))
        data['issue_types'] = ', '.join(sorted(data['issue_types']))
        final_rows.append(data)

    print(f"\n--- Writing {len(final_rows)} unique rows to CSV ---")
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        # Define the columns in the requested order.
        fieldnames = [
            'custom_field_id', 'custom_field_name', 'screen_name',
            'issue_types', 'source', 'scheme_name', 'project_keys'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(final_rows)
else:
    print("\n--- No results found to write to CSV ---")

elapsed = time.time() - start_time
print(f"\nExecution complete. Audit exported to {output_file}.")
print(f"Execution time: {elapsed:.2f} seconds.")
