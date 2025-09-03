import requests
from requests.auth import HTTPBasicAuth
import csv
import time
from datetime import datetime

# --- CONFIGURATION ---
JIRA_URL = ""
USERNAME = ""
API_TOKEN = ""

API_PROJECTS_ENDPOINT = "/rest/api/3/project/search"
API_WORKFLOW_ENDPOINT = "/rest/api/3/workflowscheme/project"
DELAY_TIME = 0.2  # Reduce if you're not hitting API limits

# --- HEADERS ---
headers = {
    "Accept": "application/json"
}

# --- SESSION SETUP ---
session = requests.Session()
session.auth = HTTPBasicAuth(USERNAME, API_TOKEN)
session.headers.update(headers)


# --- FUNCTIONS ---

def get_workflow_for_project(project_id):
    url = f"{JIRA_URL}{API_WORKFLOW_ENDPOINT}?projectId={project_id}"
    response = session.get(url)
    if response.status_code != 200:
        print(f"  ⚠️ Failed to fetch workflow for project ID {project_id}. Status: {response.status_code}")
        return {"scheme_name": "N/A", "issueTypeMappings": {}}

    data = response.json()
    if "values" in data and isinstance(data["values"], list) and len(data["values"]) > 0:
        workflow_scheme = data["values"][0].get("workflowScheme", {})
        scheme_name = workflow_scheme.get("name", "N/A")
        mappings = workflow_scheme.get("issueTypeMappings", {})
        return {"scheme_name": scheme_name, "issueTypeMappings": mappings}
    else:
        return {"scheme_name": "N/A", "issueTypeMappings": {}}


def get_issue_types_for_project(project):
    issue_types = project.get('issueTypes', [])
    return {it.get('id'): it.get('name') for it in issue_types}


def get_paginated_projects():
    start_at = 0
    max_results = 50
    all_projects = []
    total_projects = None
    project_counter = 0

    print("🔄 Fetching project list...")
    while True:
        url = f"{JIRA_URL}{API_PROJECTS_ENDPOINT}?expand=lead,insight,issueTypes&startAt={start_at}&maxResults={max_results}"
        response = session.get(url)
        if response.status_code != 200:
            print(f"❌ Failed to fetch projects. Status: {response.status_code}")
            break

        data = response.json()
        total_projects = total_projects or data.get('total', 0)
        projects = data.get('values', [])

        for project in projects:
            project_counter += 1
            print(f"▶️ Processing project {project_counter}/{total_projects} - {project.get('key')}")

            project_id = project.get('id')
            insight = project.get('insight', {})
            issue_type_map = get_issue_types_for_project(project)

            # Format last update date
            last_raw = insight.get('lastIssueUpdateTime', 'N/A')
            try:
                last_updated = datetime.strptime(last_raw, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%d-%m-%Y")
            except:
                last_updated = "N/A"

            # Get workflow scheme and mappings
            workflow_data = get_workflow_for_project(project_id)
            scheme_name = workflow_data.get("scheme_name", "N/A")
            mappings = workflow_data.get("issueTypeMappings", {})

            # Build row per workflow mapping
            for issue_type_id, workflow_name in mappings.items():
                issue_type_name = issue_type_map.get(issue_type_id, "Unknown")

                row = {
                    "Project Key": project.get('key'),
                    "Project ID": project.get('id'),
                    "Project Name": project.get('name'),
                    "Project Lead": project.get('lead', {}).get('displayName', 'N/A'),
                    "totalIssueCount": insight.get('totalIssueCount', 'N/A'),
                    "lastIssueUpdateTime": last_updated,
                    "Workflow Scheme": scheme_name,
                    "Assigned Workflow": workflow_name,
                    "issueTypes": issue_type_name
                }
                all_projects.append(row)

            print(f"  ✔️ Added {len(mappings)} workflow mappings")

        if len(projects) < max_results:
            break

        start_at += max_results
        time.sleep(DELAY_TIME)

    return all_projects


def export_to_csv(projects, file_name="jira_projects_with_workflows.csv"):
    headers = ["Project Key", "Project ID", "Project Name", "Project Lead", "totalIssueCount",
               "lastIssueUpdateTime", "Workflow Scheme", "Assigned Workflow", "issueTypes"]
    with open(file_name, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        for project in projects:
            writer.writerow(project)


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    projects = get_paginated_projects()
    export_to_csv(projects)
    print(f"\n✅ Exported {len(projects)} rows to 'jira_projects_with_workflows.csv'")
