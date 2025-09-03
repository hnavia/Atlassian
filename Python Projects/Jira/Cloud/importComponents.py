import requests
from requests.auth import HTTPBasicAuth
import json
import csv
from datetime import datetime

######################################################################
# Enter your admin email, token and baseurl without the /
######################################################################
user = 'EMAIL'
token = 'TOKEN'
baseurl = 'BASEURL'
######################################################################

file = open("components.csv", "r")
reader = csv.reader(file)
next(reader) #so we skip the first line

logfile = open("log_components.csv", "a", encoding="utf8")
logfile.write("Time,Name,Description,Project,Code,Message")
logfile.write("\n")


for line in reader:
   url = baseurl + "/rest/api/3/component"

   auth = HTTPBasicAuth(user, token)

   headers = {
      "Accept": "application/json",
      "Content-Type": "application/json"
   }

   payload = json.dumps({
       "assigneeType": line[0],
       "description": line[4],
       "isAssigneeTypeValid": line[1],
       "leadAccountId": line[5],
       "name": line[2],
       "project": line[3]
   })

   response = requests.request(
      "POST",
      url,
      data=payload,
      headers=headers,
      auth=auth
   )
   #print(response.text)

   finalerrormessage = ""
   if (response.status_code == 201 or response.status_code == 200):
      finalerrormessage = "Successful"
   else:
      finalerrormessage = response.json()["errorMessages"][0]
   logfile.write(f'{str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))},{str(line[2])},"{str(line[4])}","{str(line[3])}",{str(response.status_code)},{finalerrormessage}')
   logfile.write("\n")
   print(f'{str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))},{str(line[2])},"{str(line[4])}","{str(line[3])}",{str(response.status_code)},{finalerrormessage}')