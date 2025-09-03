import requests
from requests.auth import HTTPBasicAuth

# Enter a user with admin rights and an Atlassian Cloud Token
user = '***'
token = '***'
# Enter the desired location where the CSV file will be created and the name of the file
csv_location = '/path/to/file/permissions.csv'
# Enter the cloud instance URL without the last "/" character
baseurl = 'https://domain.atlassian.net'
auth = HTTPBasicAuth(user, token)


csv_file = open(csv_location, 'a', encoding='utf-8')
csv_file.write('Project ID,Project Name,Project Key,Permission Scheme,Permission Scheme ID')
csv_file.write("\n")

url_proj = baseurl + "/rest/api/3/project/search"

headers = {
    "Accept": "application/json",
    }

response_max = requests.request(
        "GET",
        url_proj,
        headers=headers,
        auth=auth
    ).json()['total']

i = 0

for i in range(response_max):
    url = baseurl + "/rest/api/3/project/search" + "?maxResults=1" + "&startAt=" + str(i + 1)
    headers = {
        "Accept": "application/json",
    }

    pkey = requests.request(
        "GET",
        url,
        headers=headers,
        auth=auth
    )

    p = pkey.json()


    for v in p['values']:
        url = baseurl + "/rest/api/3/project/" + v['key'] + "/permissionscheme"
        headers = {
            "Accept": "application/json",
        }

        pscheme = requests.request(
            "GET",
            url,
            headers=headers,
            auth=auth
        )

        perm = pscheme.json()

        csv_file.write(f'{v["id"]},{v["name"]},{v["key"]},{perm["name"]},{perm["id"]}')
        csv_file.write("\n")
        print(f'{v["id"]},{v["name"]},{v["key"]},{perm["name"]},{perm["id"]}')
csv_file.close()
