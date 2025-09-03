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
pword = ''
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

file = open(csv_file, 'r')
reader = csv.reader(file)
next(reader)  # so we skip the first line

logfile = open(log, 'a', encoding='utf8')
logfile.write('Time,Project,Name,Role Name,Role ID,Code,Message')
logfile.write('\n')

s = requests.Session()

s.auth = HTTPBasicAuth(user, pword)

s.headers.update({
    'Accept': 'application/json',
    'Content-Type': 'application/json'
})

for line in reader:
    if line[3] == 'atlassian-group-role-actor':
        payload = json.dumps({
            "group": [line[4]]
        })

        resp = s.post(baseurl + '/rest/api/2/project/' + line[2] + '/role/' + line[0], data=payload)

        print(line[0], line[3], line[4], resp)

    elif line[3] == 'atlassian-user-role-actor':
        payload = json.dumps({
            'user': [line[4]]
        })

        resp = s.post(baseurl + '/rest/api/2/project/' + line[2] + '/role/' + line[0], data=payload)

        print(line[0], line[3], line[4], resp)

        finalerrormessage = ''
        if resp.status_code == 201 or resp.status_code == 200:
            finalerrormessage = 'Successful'
        else:
            finalerrormessage = resp.json()['errorMessages'][0]
        logfile.write(f'{str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))},{str(line[2])},{str(line[4])},{str(line[1])},{str(line[0])},{str(resp.status_code)},{finalerrormessage}')
        logfile.write("\n")
        print(f'{str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))},{str(line[2])},{str(line[4])},{str(line[1])},{str(line[0])},{str(resp.status_code)},{finalerrormessage}')

print(time.time() - start, 'seconds')
