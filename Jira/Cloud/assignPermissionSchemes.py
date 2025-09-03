import requests
from requests.auth import HTTPBasicAuth
import json
import csv
from datetime import datetime
import time

start = time.time()

######################################################################
# Enter your admin email, token and baseurl without the /
######################################################################
user = 'email'
token = 'token'
baseurl = 'baseurl'
######################################################################
######################################################################
# Enter the CSV file path and name with the data
csv_file = 'permissions.csv'
######################################################################
######################################################################
# Enter the CSV path (optional) and name of the log file
log = 'log_assignperm.csv'
######################################################################

file = open(csv_file, 'r')
reader = csv.reader(file)
next(reader)  # so we skip the first line

logfile = open(log, 'a', encoding='utf8')
logfile.write('Time,Project ID, Project Name,Project Key,Permission Scheme,PS ID,Code,Message')
logfile.write('\n')

s = requests.Session()

s.auth = HTTPBasicAuth(user, token)

s.headers.update({
    'Accept': 'application/json',
    'Content-Type': 'application/json'
})

for line in reader:
    pkey = line[2]

    payload = json.dumps({
        'id': line[4]
    })

    resp = s.put(baseurl + '/rest/api/3/project/' + pkey + '/permissionscheme', data=payload)

    finalerrormessage = ''
    if resp.status_code == 204 or resp.status_code == 200:
        finalerrormessage = 'Successful'
    else:
        finalerrormessage = resp.json()['errorMessages'][0]
    logfile.write(
        f'{str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))},{line[0]},{line[1]},{line[2]},"{line[3]}",{line[4]},{str(resp.status_code)},{finalerrormessage}')
    logfile.write("\n")
    print(
        f'{str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))},{line[0]},{line[1]},{line[2]},"{line[3]}",{line[4]},{str(resp.status_code)},{finalerrormessage}')

print(time.time() - start, 'seconds')
