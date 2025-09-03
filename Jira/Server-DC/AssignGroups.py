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
csv_file = ''
######################################################################
######################################################################
# Enter the CSV path (optional) and name of the log file
log = ''
######################################################################

start = time.time()

file = open(csv_file, 'r')
reader = csv.reader(file)
next(reader)  # so we skip the first line

logfile = open(log, 'a', encoding='utf8')
logfile.write('Time,User,Group,Code,Message')
logfile.write('\n')

s = requests.Session()

s.auth = HTTPBasicAuth(user, pword)

s.headers.update({
    'Accept': 'application/json',
    'Content-Type': 'application/json'
})

for line in reader:
    query = {
        'groupname': line[0]
    }

    payload = json.dumps({
        'name': line[1]
    })

    resp = s.post(baseurl + '/rest/api/2/group/user', params=query, data=payload)

    if resp.status_code == 201 or resp.status_code == 200:
        finalerrormessage = 'Successful'
    else:
        finalerrormessage = resp.json()['errorMessages'][0]
    logfile.write(f'{str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))},{str(line[1])},{str(line[0])},{str(resp.status_code)},{finalerrormessage}')
    logfile.write("\n")

    print(f'{str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))},{str(line[1])},{str(line[0])},{str(resp.status_code)},{finalerrormessage}')

print(time.time() - start, 'seconds')
