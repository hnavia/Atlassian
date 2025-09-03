import requests
from requests.auth import HTTPBasicAuth

######################################################################
# Enter your admin username, password and baseurl without the /
######################################################################
user = ''
pword = ''
baseurl = ''
######################################################################

bauth = HTTPBasicAuth(user, pword)

csv_file = open('swpermissions.csv', 'a', encoding='utf-8')
csv_file.write('Project ID,Project Name,Project Key,Permission Scheme,Permission Scheme ID')
csv_file.write('\n')

purl = baseurl + '/rest/api/2/project'

headers = {
    'Accept': 'application/json',
    }

presponse = requests.request(
        'GET',
        purl,
        headers=headers,
        auth=bauth
    ).json()

ptotal = len(presponse)
#print(ptotal)

i = 0

for i in range(ptotal):
    permurl = baseurl + '/rest/api/2/project/' + presponse[i]['key'] + '/permissionscheme'

    permreturn = requests.request(
        'GET',
        permurl,
        headers=headers,
        auth=bauth
    )

    pscheme = permreturn.json()

    csv_file.write(f'{presponse[i]["id"]},"{presponse[i]["name"]}",{presponse[i]["key"]},{pscheme["name"]},{pscheme["id"]}')
    csv_file.write('\n')
    print(presponse[i]['id'], presponse[i]['name'], presponse[i]['key'], pscheme['name'], pscheme['id'])
csv_file.close()