import os
import requests
from requests.auth import HTTPBasicAuth
import re
import time
from datetime import datetime

# Enter your admin email, token, and baseurl without the /
user = ''
token = ''
baseurl = ''

# Enter the CSV file path (optional) and name where to save the data
csv_file = 'attInfo.csv'

# Enter the date to filter attachments (format: 'YYYY-MM-DD')
remove_attachments_before_date = '2018-09-01'

# Flags to control behavior
export_attachments = True  # Set to False if you don't want to export attachments
remove_attachments = False  # Set to True if you want to remove attachments based on dates

start = time.time()

file = open(csv_file, 'a', encoding='utf-8')
file.write('Issue,Author,File Name,Size,Upload Date')
file.write('\n')

# Create a session with Jira API
s = requests.Session()
s.auth = HTTPBasicAuth(user, token)
s.headers.update({
    'Accept': 'application/json',
})

# Get issues with attachments
resp = s.get(baseurl + '/rest/api/2/search?jql=attachments%20is%20not%20EMPTY&fields=attachment')
if resp.status_code == 200:
    resp_max = resp.json()['total']
else:
    print(f"Failed to retrieve issues with attachments. Status code: {resp.status_code}")
    resp_max = 0

# Parse the remove_attachments_before_date string to a datetime object
remove_before_date = datetime.strptime(remove_attachments_before_date, '%Y-%m-%d')

# Loop through issues
for i in range(resp_max):
    at_url = s.get(baseurl + f'/rest/api/2/issue/{i}')
    at_resp = at_url.json()

    at_total = len(at_resp['fields']['attachment'])
    at_dir = at_resp['fields']['project']['key']

    if not os.path.isdir('Attachments/' + at_dir):
        os.makedirs('Attachments/' + at_dir)

    for a in range(at_total):
        i_key = at_resp['key']
        attachment = at_resp['fields']['attachment'][a]
        att_url = attachment['content']
        att_name = attachment['filename']
        att_size = attachment['size'] / 1048576
        att_author = attachment['author']['displayName']
        att_created = attachment['created']
        date_created = re.sub(r'T.*', '', att_created)

        # Parse the attachment creation date string to a datetime object
        attachment_created_date = datetime.strptime(date_created, '%Y-%m-%d')

        # Check if the attachment should be processed based on the given date
        should_process_attachment = (
            (not remove_attachments) or
            (remove_attachments and (attachment_created_date <= remove_before_date))
        )

        if should_process_attachment:
            # Create a directory for the issue if it doesn't exist
            issue_dir = os.path.join('Attachments', at_dir, i_key)
            if not os.path.exists(issue_dir):
                os.makedirs(issue_dir)

            # Download the attachment and save it if export_attachments is True
            if export_attachments:
                response = s.get(att_url)
                if response.status_code == 200:
                    with open(os.path.join(issue_dir, att_name), 'wb') as f:
                        f.write(response.content)
                        print(f"Downloaded {att_name} for issue {i_key}")
                else:
                    print(f"Failed to download attachment {att_name} for issue {i_key}")

            # Write information to CSV
            file.write(f"{i_key},{att_author},{att_name},{att_size},{date_created}")
            file.write("\n")
            print(f"{i_key},{att_author},{att_name},{att_size},{date_created}")

file.close()

# Optionally, you can calculate the total time taken
print(time.time() - start, 'seconds')
