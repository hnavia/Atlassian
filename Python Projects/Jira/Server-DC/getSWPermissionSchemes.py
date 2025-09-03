import requests
import json
from requests.auth import HTTPBasicAuth

######################################################################
# Enter your admin username, password and baseurl without the /
######################################################################
user = 'USER'
pword = 'PASS'
baseurl = ''
######################################################################

bauth = HTTPBasicAuth(user, pword)

csv_file = open('swpermissions.csv', 'a', encoding='utf-8')
csv_file.write('PS ID,PS Name,PS Description,Permissions')
csv_file.write("\n")

purl = baseurl + '/rest/api/2/permissionscheme'

headers = {
    'Accept': 'application/json',
}

presponse = requests.request(
    'GET',
    purl,
    headers=headers,
    auth=bauth
).json()['permissionSchemes']

ptotal = len(presponse)
print(ptotal)

i = 0

for i in range(1):
    permurl = baseurl + '/rest/api/2/permissionscheme/' + str(presponse[i]['id'])

    query = {
        'expand': 'all'
    }

    permreturn = requests.request(
        'GET',
        permurl,
        headers=headers,
        params=query,
        auth=bauth
    )

    pscheme = permreturn.json()
    # permission = pscheme['permissions']
    permission = json.dumps(pscheme['permissions'])

    vtotal = len(permission)
    print(vtotal)

    for n in range(vtotal):
        try:
            holder_parameter = pscheme['permissions'][n]['holder']['parameter']
            holder_type = pscheme['permissions'][n]['holder']['type']
            holder_name = pscheme['permissions'][n]['holder']['projectRole']['name']
            holder_permission = pscheme['permissions'][n]['permission']
            csv_file.write(f'{pscheme["id"]},{pscheme["name"]},"{pscheme["description"]}","""{permission}"""')
            csv_file.write("\n")
            print(pscheme['name'], holder_parameter, holder_type, holder_name, holder_permission)
        except KeyError:
            holder_parameter = pscheme['permissions'][n]['holder']['parameter']
            holder_name = pscheme['permissions'][n]['holder']['projectRole']['name']
            holder_permission = pscheme['permissions'][n]['permission']
            csv_file.write(f'{pscheme["id"]},{pscheme["name"]},"","""{permission}"""')
            csv_file.write("\n")
            print(pscheme['name'], holder_parameter, holder_name, holder_permission)
# csv_file.close()
