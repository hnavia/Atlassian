import requests
import csv
from requests.auth import HTTPBasicAuth

# ========= CONFIGURATION =========
user = ''
token = ''
baseurl = ''
csv_file = r''
page_size = 50  # Max allowed by Jira
# =================================

baseurl = baseurl.rstrip('/')
auth = HTTPBasicAuth(user, token)
headers = {'Accept': 'application/json'}

# ========= FIELD TYPE MAPPING =========
field_type_mapping = {
    "com.atlassian.jira.plugin.system.customfieldtypes:multicheckboxes": "Checkboxes",
    "com.atlassian.jira.plugin.system.customfieldtypes:datepicker": "Date Picker",
    "com.atlassian.jira.plugin.system.customfieldtypes:datetime": "Date Time Picker",
    "com.atlassian.jira.plugin.system.customfieldtypes:labels": "Labels",
    "com.atlassian.jira.plugin.system.customfieldtypes:float": "Number Field",
    "com.atlassian.jira.plugin.system.customfieldtypes:project": "Project Picker (single project)",
    "com.atlassian.jira.plugin.system.customfieldtypes:radiobuttons": "Radio Buttons",
    "com.atlassian.jira.plugin.system.customfieldtypes:cascadingselect": "Select List (cascading)",
    "com.atlassian.jira.plugin.system.customfieldtypes:multiselect": "Select List (multiple choices)",
    "com.atlassian.jira.plugin.system.customfieldtypes:select": "Select List (single choice)",
    "com.atlassian.jira.plugin.system.customfieldtypes:textarea": "Text Field (multi-line)",
    "com.atlassian.jira.plugin.system.customfieldtypes:textfield": "Text Field (single line)",
    "com.atlassian.jira.plugin.system.customfieldtypes:url": "URL Field",
    "com.atlassian.jira.plugin.system.customfieldtypes:multiuserpicker": "User Picker (multiple users)",
    "com.atlassian.jira.plugin.system.customfieldtypes:userpicker": "User Picker (single user)",
    "com.atlassian.jira.plugins.proforma-managed-fields:forms-locked-field-cftype": "Locked forms",
    "com.atlassian.plugins.atlassian-connect-plugin:io.tempo.jira__account": "Account",
    "com.atlassian.servicedesk.approvals-plugin:sd-approvals": "Approvals",
    "com.atlassian.jira.plugin.system.customfieldtypes:jwm-category": "JWM-Category",
    "com.atlassian.jira.ext.charting:firstresponsedate": "Date of First Response",
    "com.atlassian.jira.ext.charting:timeinstatus": "Time in Status",
    "com.atlassian.jira.plugins.jira-development-integration-plugin:designcf": "Design",
    "com.atlassian.jira.plugins.jira-development-integration-plugin:devsummarycf": "Dev Summary Custom Field",
    "com.pyxis.greenhopper.jira:gh-epic-color": "Color of Epic",
    "com.pyxis.greenhopper.jira:gh-epic-link": "Epic Link Relationship",
    "com.pyxis.greenhopper.jira:gh-epic-label": "Name of Epic",
    "com.pyxis.greenhopper.jira:gh-epic-status": "Status of Epic",
    "com.atlassian.jira.plugin.system.customfieldtypes:goals": "Goals",
    "com.pyxis.greenhopper.jira:jsw-issue-color": "Issue color",
    "com.atlassian.jconnect.jconnect-plugin:location": "Custom Google Map Field",
    "com.atlassian.jira.plugins.proforma-managed-fields:forms-open-field-cftype": "Open forms",
    "com.atlassian.servicedesk:sd-customer-organizations": "Organizations",
    "com.atlassian.jpo:jpo-custom-field-parent": "Parent Link",
    "com.pyxis.greenhopper.jira:gh-lexo-rank": "Global Rank",
    "com.atlassian.servicedesk.servicedesk-lingo-integration-plugin:sd-request-language": "Request language",
    "com.atlassian.servicedesk:sd-request-participants": "Request Participants",
    "com.atlassian.servicedesk:vp-origin": "Customer Request Type Custom Field",
    "com.atlassian.servicedesk:sd-request-feedback": "Satisfaction",
    "com.atlassian.servicedesk:sd-request-feedback-date": "Satisfaction date",
    "com.atlassian.servicedesk.sentiment:sd-sentiment": "Sentiment",
    "com.pyxis.greenhopper.jira:gh-sprint": "Jira Sprint Field",
    "com.pyxis.greenhopper.jira:jsw-story-points": "Story point estimate value",
    "com.atlassian.jira.plugins.proforma-managed-fields:forms-submitted-field-cftype": "Submitted forms",
    "com.atlassian.jpo:jpo-custom-field-baseline-end": "Target end",
    "com.atlassian.jpo:jpo-custom-field-baseline-start": "Target start",
    "com.atlassian.jira.plugin.system.customfieldtypes:atlassian-team": "Team Picker (single team)",
    "com.atlassian.plugins.atlassian-connect-plugin:io.tempo.jira__team": "Tempo Team",
    "com.atlassian.servicedesk:sd-sla-field": "SLA CustomField Type",
    "com.atlassian.jira.plugins.proforma-managed-fields:forms-total-field-cftype": "Total forms",
    "com.atlassian.jconnect.jconnect-plugin:uuid": "UUID Field",
    "com.atlassian.jira.plugins.jira-development-integration-plugin:vulnerabilitycf": "Vulnerability",
    "com.atlassian.jira.plugins.service-entity:service-entity-field-cftype": "Service entity field",
    "com.atlassian.plugins.atlassian-connect-plugin:com.servicerocket.jira.salesforce__association-count-field": "Association Count",
    "jira.polaris:atlassian-project": "Project (Jira Product Discovery)",
    "jira.polaris:atlassian-project-status": "Project Status (Jira Product Discovery)",
    "jira.polaris:count-issue-comments": "Comments (Jira Product Discovery)",
    "jira.polaris:delivery-progress": "Delivery Progress (Jira Product Discovery)",
    "jira.polaris:delivery-status": "Delivery Status (Jira Product Discovery)",
    "com.atlassian.jira.plugin.system.customfieldtypes:version": "Version Picker (single version)",
    "com.atlassian.jira.plugin.system.customfieldtypes:people": "User Picker (multiple users)",
    "jira.polaris:count-insights": "Insights (Jira Product Discovery)",
    "com.atlassian.jira.plugin.system.customfieldtypes:multiversion": "Version Picker (multiple version)",
    "jira.polaris:count-linked-issues": "Linked Issues (Jira Product Discovery)",
    "read-only-string-issue-field": "Read only text field",
    "com.atlassian.jira.modules.servicemanagement.major-incident-entity:major-incident-entity-field-cftype": "Major incident entity field",
    "com.atlassian.jira.modules.servicemanagement.responders-entity:responders-entity-field-cftype": "Responders",
    "com.atlassian.jira.plugin.system.customfieldtypes:multigrouppicker": "Group Picker (multiple groups)",
    "com.atlassian.jira.plugins.work-category-field:work-category-field-cftype": "Work Category",
    "com.atlassian.plugins.atlassian-connect-plugin:com.gebsun.plugins.jira.issuechecklist__issue-checklist-templates": "Checklist Template",
    "read-only-number-issue-field": "Read only number field",
    "com.atlassian.plugins.atlassian-connect-plugin:com.intenso.jira.issue-templates__template": "Template",
    "com.atlassian.jira.plugin.system.customfieldtypes:grouppicker": "Group Picker (single group)",
    "com.atlassian.plugins.atlassian-connect-plugin:foxly__score": "Priority Score",
    "com.atlassian.jira.plugin.system.customfieldtypes:readonlyfield": "Text Field (read only)",
    "com.atlassian.jira.plugins.jira-development-integration-plugin:devsummary": "Development Summary",
    "com.atlassian.jpo:jpo-custom-field-original-story-points": "Original story points",
    "com.atlassian.servicedesk.incident-management-plugin:sd-incidents-link": "Linked major incidents",
    "com.atlassian.teams:rm-teams-custom-field-team": "Team",
    "com.burningcode.jira.issue.customfields.impl.jira-watcher-field:watcherfieldtype": "Watcher Field",
    "com.iamhuy.jira.plugin.issue-alternative-assignee:userselectbox-customfield": "User Picker (single user)",
    "com.intenso.jira.issue-templates:issue-templates-customfield": "Deviniti [Issue Templates] - Template Selection",
    "com.intenso.jira.plugins.jsd-extender:jsd-rich-text": "Deviniti [Extension] - Rich Text",
    "com.j-tricks.jql-plugin:jqlt-field": "Jqlt Field",
    "com.onresolve.jira.groovy.groovyrunner:jqlFunctionsCustomFieldType": "JQL Functions Customfield Type",
    "com.onresolve.jira.groovy.groovyrunner:scripted-field": "Scripted Field",
    "com.pyxis.greenhopper.jira:gh-global-rank": "Global Rank (obsolete)",
    "com.pyxis.greenhopper.jira:greenhopper-releasedmultiversionhistory": "Version Picker (multiple versions)",
    "com.riadalabs.jira.plugins.insight:rlabs-customfield-default-object": "Assets object",
    "com.riadalabs.jira.plugins.insight:rlabs-customfield-object-reference": "Assets referenced object (single)",
    "com.riadalabs.jira.plugins.insight:rlabs-customfield-object-reference-multi": "Assets referenced object (multiple)",
    "com.tempoplugin.tempo-accounts:accounts.customfield": "Tempo Accounts Custom Field",
    "com.tempoplugin.tempo-plan-core:tp.iteration.customfield": "Iteration",
    "com.tempoplugin.tempo-teams:team.customfield": "Team",
    "com.tempoplugin.tempo-teams:team.role.customfield": "Team Role",
    "is.origo.jira.tempo-plugin:billingKeys": "Tempo Account",
    "plugin.tts:overduestatusDbVersion": "TTS - Overdue Status",
    "plugin.tts:sla-elapsed-duration-sorter-cf": "TTS - SLA Elapsed Duration Sorter",
    "plugin.tts:sla-end-date-sorter-cf": "TTS - SLA End Date Sorter",
    "plugin.tts:sla-function-cf": "TTS - SLA Function",
    "plugin.tts:sla-remaining-duration-sorter-cf": "TTS - SLA Remaining Duration Sorter",
    "plugin.tts:sla-start-date-sorter-cf": "TTS - SLA Start Date Sorter",
    "plugin.tts:sla-target-date-sorter-cf": "TTS - SLA Target Date Sorter",
    "plugin.tts:timetoSlaDbVersion": "TTS - Time to SLA",
    "ru.mail.jira.plugins.todolist:todo-list-custom-field": "ToDo List custom field",
    "rw-smart-checklist-biz:railsware-smartchecklist-customfield": "Smart Checklist Custom Field",
    "rs.codecentric.label-manager-project:labelManagerCustomField": "Label Manager",
}
# ======================================

# Get total number of fields (for progress display)
total_resp = requests.get(f"{baseurl}/rest/api/3/field/search", headers=headers, auth=auth)
total = total_resp.json().get("total", 0)

with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['ID', 'Name', 'Description', 'Field Type', 'Screens Count', 'Issue Count', 'Tracked?', 'Last Used'])

    start_at = 0
    processed = 0

    while True:
        params = {
            "startAt": start_at,
            "maxResults": page_size,
            "expand": "lastUsed,screensCount"
        }
        response = requests.get(f"{baseurl}/rest/api/3/field/search", headers=headers, params=params, auth=auth)

        if response.status_code != 200:
            print(f"Error retrieving fields: {response.status_code}")
            break

        data = response.json()
        fields = data.get("values", [])

        for v in fields:
            processed += 1
            cf_id = v.get("id", "")
            name = v.get("name", "")
            description = v.get("description", "")
            screens = v.get("screensCount", "")
            last_used = v.get("lastUsed", {})
            tracked = last_used.get("type", "")
            last_used_date = last_used.get("value", "")[:10] if last_used.get("value") else ""

            schema = v.get("schema", {})
            if 'custom' in schema:
                type_key = schema.get("custom")
                field_type = field_type_mapping.get(type_key, type_key)
            else:
                field_type = "System field"

            issue_count = ""
            if 'customId' in schema:
                jql_url = f"{baseurl}/rest/api/3/search?jql=cf[{schema['customId']}] IS NOT EMPTY&maxResults=0"
                jql_resp = requests.get(jql_url, headers=headers, auth=auth)
                if jql_resp.status_code == 200:
                    issue_count = jql_resp.json().get("total", 0)
                else:
                    issue_count = "Error"

            row = [cf_id, name, description, field_type, screens, issue_count, tracked, last_used_date]
            writer.writerow(row)

            status_icon = "✅" if issue_count != "Error" else "⚠️"
            print(f"[ {processed} / {total} ] {cf_id} - {name} - Type: {field_type} - Issue Count: {issue_count} - {status_icon}")

        if data.get("isLast", True):
            break
        start_at += page_size

print(f"\n✅ Export completed. {processed} fields written to '{csv_file}'")
