import requests
from requests.auth import HTTPBasicAuth
import json
import csv
from datetime import datetime

user = ""
token = ""
baseurl = ""

file = open("cflist_fixed.csv", "r")
reader = csv.reader(file)
next(reader)  # so we skip the first line

logfile = open("log_cffixed.csv", "a", encoding="utf8")
logfile.write("Time,ID,Name,Description,Code,Message")
logfile.write("\n")

for line in reader:
    rurl = line[0]
    url = baseurl + "/rest/api/3/field/" + rurl

    auth = HTTPBasicAuth(user, token)

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = json.dumps({
        "description": line[2]
    })

    response = requests.request(
        "PUT",
        url,
        data=payload,
        headers=headers,
        auth=auth
    )

    finalerrormessage = ""
    if response.status_code == 204 or response.status_code == 200:
        finalerrormessage = "Successful"
        print("Successful")
    else:
        finalerrormessage = response.json()["errorMessages"][0]
        print(f'{str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))},{line[0]},"{line[1]}","{line[2]}",{str(response.status_code)},{finalerrormessage}')

    logfile.write(f'{str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))},{line[0]},"{line[1]}","{line[2]}",{str(response.status_code)},{finalerrormessage}')
    logfile.write("\n")
logfile.close()
