import requests
from requests.auth import HTTPBasicAuth
import csv
import time

# ========= CONFIGURATION =========
user = 'your_email@example.com'               # Jira user / email
token = 'your_api_token'                      # Jira API token
baseurl = 'https://your-instance.atlassian.net/'
csv_file = r'D:\path\Workflows_Audit.csv'     # Output CSV
keywords_to_search = ['jmwe']                 # ← add / remove keywords here
page_size = 50                                # Max allowed by Jira
# =================================

baseurl = baseurl.rstrip('/')                 # ← keep to avoid double “//”

# ---------- Helper: REST call (with basic error handling) ----------
def make_request(session, url):
    try:
        response = session.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"[HTTP {e.response.status_code}] {url}")
    except requests.exceptions.RequestException as e:
        print(f"[Request Error] {url}: {e}")
    return None


# ---------- Helper: paginate any Jira endpoint ----------
def get_paginated_data(session, api_path, query_string=''):
    """
    Fetch all pages for the given endpoint.
    api_path – e.g. '/rest/api/3/workflow/search'
    query_string – everything after '?', without startAt / maxResults
    """
    start_at = 0
    results  = []

    while True:
        url = (
            f"{baseurl}{api_path}?{query_string}"
            f"&startAt={start_at}&maxResults={page_size}"
        )
        data = make_request(session, url)
        if not data:
            break

        batch = data.get("values", [])
        results.extend(batch)

        # end‑of‑data check
        if data.get("isLast", True) or not batch:
            break
        start_at += page_size

    return results


# ---------- Helper: extract keyword hits ----------
def extract_plugin_hits(workflow, keywords):
    """
    Returns a list of rows [workflow_name, transition, keyword, function_type]
    where keyword matches any rule type in validators / postFunctions / conditions.
    """
    output = []
    wf_name = workflow["id"]["name"]

    for transition in workflow.get("transitions", []):
        trans_id   = transition["id"]
        trans_name = transition["name"]
        trans_info = f"{trans_name} ({trans_id})"

        # Scan the rule containers we care about
        for container, label in (
            ("validators",    "validator"),
            ("postFunctions", "post-function"),
            ("conditions",    "condition"),
        ):
            for rule in transition.get("rules", {}).get(container, []):
                rule_type_lc = rule.get("type", "").lower()
                for kw in keywords:
                    if kw in rule_type_lc:
                        output.append([wf_name, trans_info, kw, label])
                        break  # no need to check more keywords for this rule

    return output


# ====================== MAIN LOGIC ======================
t0 = time.time()
session = requests.Session()
session.auth = HTTPBasicAuth(user, token)
session.headers.update({'Accept': 'application/json'})

print("📥  Fetching active workflows …")
workflows = get_paginated_data(
    session,
    '/rest/api/3/workflow/search',
    'expand=transitions.rules,statuses,operations&isActive=true'
)
print(f"   → {len(workflows)} workflows retrieved.\n")

rows = []
for i, wf in enumerate(workflows, 1):
    print(f"🔎 [{i}/{len(workflows)}]  {wf['id']['name']}")
    rows.extend(extract_plugin_hits(wf, keywords_to_search))

# ---------- Write CSV ----------
with open(csv_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Workflow Name', 'Transition', 'Keyword', 'Function Type'])
    writer.writerows(rows)

print("\n✅  Done:")
print(f"   • {len(rows)} matching entries written to {csv_file}")
print(f"   • Elapsed time: {time.time() - t0:.1f}s")
