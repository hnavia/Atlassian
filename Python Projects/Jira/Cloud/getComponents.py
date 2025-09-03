import requests
from requests.auth import HTTPBasicAuth

######################################################################
# Enter your admin email, token and baseurl without the /
######################################################################
user = 'EMAIL'
token = 'TOKEN'
baseurl = 'BASEURL'
######################################################################

# Enter all the project keys in single quotes and separated by commas. IE: 'PKEY1', 'PKEY2', 'PKEY3'
pkey = ['PKEY1', 'PKEY2', 'PKEY3']

auth = HTTPBasicAuth(user, token)

csv_file = open("components.csv", "a", encoding="utf-8")
csv_file.write("assigneeType,isAssigneeTypeValid,name,project,Description,leadAccountId,displayName")
csv_file.write("\n")


for p in pkey:
    response_max = baseurl + "/rest/api/3/project/" + p + "/component"
    headers = {
        "Accept": "application/json",
    }

    response_max = requests.request(
        "GET",
        response_max,
        headers=headers,
        auth=auth
    ).json()['total']
    print(response_max)

    i = 0

    for i in range(response_max):
        url_max = baseurl + "/rest/api/3/project/" + p + "/component" + "?maxResults=1" + "&startAt=" + str(i)

        response = requests.request(
            "GET",
            url_max,
            headers=headers,
            auth=auth
        )
        d = response.json()['values']
        for v in d:
            try:
                description = v['description']
            except KeyError:
                description = ""

            try:
                lead = v['lead']['accountId']
                #leadid = lead['accountId']
            except KeyError:
                lead = ""

            try:
                dname = v['lead']['displayName']
                #lname = dname['displayName']
            except KeyError:
                dname = ""


            csv_file.write(f'{v["assigneeType"]},{str(v["isAssigneeTypeValid"]).lower()},"{v["name"]}","{v["project"]}","{description}",{lead},{dname}')
            csv_file.write("\n")
            print(f'{v["assigneeType"]},{str(v["isAssigneeTypeValid"]).lower()},"{v["name"]}","{v["project"]}","{description}",{lead},{dname}')
csv_file.close()