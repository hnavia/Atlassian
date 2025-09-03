import requests
from requests.auth import HTTPBasicAuth
import json
import csv
from datetime import datetime

user = ""
token = ""
baseurl = ""


file=open("D:/filters.csv", "r")
reader=csv.reader(file)
next(reader) #so we skip the first line

logfile=open("D:\logfile.csv","a",encoding="utf8")
logfile.write("Time,Name,Description,JQL,Code,Message")
logfile.write("\n")


for line in reader:
   url = baseurl + "/rest/api/3/filter"

   auth = HTTPBasicAuth(user, token)

   headers = {
      "Accept": "application/json",
      "Content-Type": "application/json"
   }

   payload = json.dumps({
      "description": str(line[1]),
      "jql": str(line[2]),
      "name": str(line[0])
   })

   response = requests.request(
      "POST",
      url,
      data=payload,
      headers=headers,
      auth=auth
   )

   finalerrormessage = ""
   if (response.status_code == 204 or response.status_code == 200):
      finalerrormessage = "Successful"
   else:
      finalerrormessage = response.json()["errorMessages"][0]
   logfile.write(f'{str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))},{str(line[0])},"{str(line[1])}","{str(line[2])}",{str(response.status_code)},{finalerrormessage}')
   logfile.write("\n")
   print(f'{str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))},{str(line[0])},"{str(line[1])}","{str(line[2])}",{str(response.status_code)},{finalerrormessage}')