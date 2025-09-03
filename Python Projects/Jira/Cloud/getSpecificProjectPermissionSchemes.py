import requests
from requests.auth import HTTPBasicAuth


# Enter a user with admin rights and an Atlassian Cloud Token
user = "***"
token = "***"
# Enter the desired location where the CSV file will be created and the name of the file
csv_location = "/path/to/file/permissions.csv"
# Enter the cloud instance URL without the last "/" character
baseurl = "https://domain.atlassian.net"
auth = HTTPBasicAuth(user, token)

#Please insert the list of Project Keys in p_key
p_key =['WPD','ADMIN','AJIIM','TBL']

csv_file = open(csv_location, "a", encoding="utf-8")
csv_file.write("Project ID,Project Name,Project Key,Permission Scheme,Permission Scheme ID")
csv_file.write("\n")

url_proj = baseurl + "/rest/api/3/project/"

headers = {
    "Accept": "application/json",
    }


for i in p_key:
    url = baseurl + "/rest/api/3/project/" + i
    purl = baseurl + "/rest/api/3/project/" + i + "/permissionscheme"
    headers = {
        "Accept": "application/json",
    }

    pkey = requests.request(
        "GET",
        url,
        headers=headers,
        auth=auth
    )

    pscheme = requests.request(
        "GET",
        purl,
        headers=headers,
        auth=auth
    )

    p = pkey.json()
    perm = pscheme.json()

    csv_file.write(f'{p["id"]},{p["name"]},{p["key"]},{perm["name"]},{perm["id"]}')
    csv_file.write("\n")
    print(f'{p["id"]},{p["name"]},{p["key"]},{perm["name"]},{perm["id"]}')
csv_file.close()