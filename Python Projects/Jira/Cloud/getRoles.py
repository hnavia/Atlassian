import requests
from requests.auth import HTTPBasicAuth

######################################################################
# Enter your admin email, token and baseurl without the /
######################################################################
user = ''
token = ''
baseurl = ''
######################################################################
######################################################################
# Enter the Project Key or Keys
######################################################################
pkey = ['A2E', 'CRM', 'DSPE']
######################################################################

auth = HTTPBasicAuth(user, token)

csv_file = open('roles.csv', 'a', encoding='utf-8')
csv_file.write('Role ID,Role Name,Project,Type,Actor ID,Actor Display Name')
csv_file.write('\n')

for p in pkey:
    roles_details = baseurl + '/rest/api/3/project/' + p + '/roledetails'

    headers = {
        'Accept': 'application/json'
    }

    roles = requests.request(
        'GET',
        roles_details,
        headers=headers,
        auth=auth
    ).json()

    r = int(len(roles))

    for i in range(r):
        rid = roles[i]['id']
        rname = roles[i]['name']
        #print(rid, rname)

        if rname == "atlassian-addons-project-access":
            continue

        r_project = baseurl + '/rest/api/3/project/' + p + '/role/' + str(rid)

        result = requests.request(
            'GET',
            r_project,
            headers=headers,
            auth=auth
        ).json()

        z = int(len(result))
        m = result['actors']
        ra = int(len(m))
        #print(ra)

        for n in range(ra):
            if m:
                try:
                    a = m[n]['type']
                    aid = m[n]['actorUser']['accountId']
                    adn = m[n]['displayName']
                    print(f'{rid},{rname},{p},{a},{aid},{adn}')
                    csv_file.write(f'{rid},{rname},{p},{a},{aid},{adn}')
                    csv_file.write("\n")
                except KeyError:
                    a = m[n]['type']
                    aid = m[n]['actorGroup']['groupId']
                    adn = m[n]['displayName']
                    print(f'{rid},{rname},{p},{a},{aid},{adn}')
                    csv_file.write(f'{rid},{rname},{p},{a},{aid},{adn}')
                    csv_file.write("\n")
            else:
                print('Empty')

csv_file.close()