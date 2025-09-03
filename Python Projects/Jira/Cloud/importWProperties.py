import requests
from requests.auth import HTTPBasicAuth
import json
import csv
from datetime import datetime
import time

######################################################################
# Enter your admin email, password and baseurl without the /
######################################################################
user = 'EMAIL'
token = 'TOKEN'
baseurl = 'BASEURL'
######################################################################
######################################################################
# Enter the path and name of the CSV file with the exported properties
csv_file = r'Properties.csv'
######################################################################
######################################################################
# Enter the location of the log file with name and CSV extension
log = r'log_wproperties.csv'
######################################################################

start = time.time()

s = requests.Session()

s.auth = HTTPBasicAuth(user, token)

s.headers.update({
    'Accept': 'application/json',
    'Content-Type': 'application/json'
})

file = open(csv_file, 'r')
reader = csv.reader(file)
next(reader)  # so we skip the first line

logfile = open(log, 'a', encoding='utf8')
logfile.write('Time,Workflow Name,T. ID,Code,Message')
logfile.write('\n')

for line in reader:
    query = {
        'key': line[2],
        'workflowName': line[1],
        'workflowMode': 'draft'
    }

    payload = json.dumps({
        'key': line[2],
        'value': line[3],
        'id': line[4]
    })

    resp = s.post(baseurl + '/rest/api/3/workflow/transitions/' + line[0] + '/properties', data=payload, params=query)

    finalerrormessage = ''
    if resp.status_code == 201 or resp.status_code == 200:
        finalerrormessage = 'Successful'
        print(f'{str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))},{str(line[1])},{str(line[0])},{str(resp.status_code)},{finalerrormessage}')
    else:
        finalerrormessage = resp.json()['errors']['key']

        logfile.write(f'{str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))},{str(line[1])},{str(line[0])},{str(resp.status_code)},{finalerrormessage}')
        logfile.write('\n')
        print(f'{str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))},{str(line[1])},{str(line[0])},{str(resp.status_code)},{finalerrormessage}')
