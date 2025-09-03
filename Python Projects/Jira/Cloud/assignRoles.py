import requests
from requests.auth import HTTPBasicAuth
import json
import csv
from datetime import datetime
import time

######################################################################
# Enter your admin email, token and baseurl without the /
######################################################################
user = ''
token = ''
baseurl = ''
######################################################################
######################################################################
# Enter the CSV file path and name with the data
csv_file = 'roles.csv'
######################################################################
######################################################################
# Enter the CSV path (optional) and name of the log file
log = 'log_assignroles.csv'
######################################################################

start = time.time()

with open(csv_file, 'r') as file, open(log, 'a', encoding='utf8') as logfile:
    reader = csv.reader(file)
    next(reader)  # Skip header

    logfile.write('Time,Project,Name,Role Name,Role ID,Code,Message\n')

    s = requests.Session()
    s.auth = HTTPBasicAuth(user, token)
    s.headers.update({
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    })

    for line in reader:
        role_id = line[0]
        role_name = line[1]
        project_key = line[2]
        actor_type = line[3]
        actor_id = line[4]
        actor_name = line[5]

        if actor_type == 'atlassian-group-role-actor':
            payload = json.dumps({ "groupId": [actor_id] })
        elif actor_type == 'atlassian-user-role-actor':
            payload = json.dumps({ "user": [actor_id] })
        else:
            continue  # Skip if unknown actor type

        resp = s.post(f'{baseurl}/rest/api/3/project/{project_key}/role/{role_id}', data=payload)

        # Default message
        if resp.status_code in [200, 201]:
            message = 'Successful'
        else:
            try:
                error_json = resp.json()
                message = error_json.get('errorMessages', ['Unknown error'])[0]
            except Exception:
                message = f"Error {resp.status_code}: {resp.text}"

        # Write log
        log_line = f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")},{project_key},{actor_name},{role_name},{role_id},{resp.status_code},{message}\n'
        logfile.write(log_line)
        print(log_line.strip())

print(f"Finished in {round(time.time() - start, 2)} seconds")
