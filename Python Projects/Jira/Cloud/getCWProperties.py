import requests
from requests.auth import HTTPBasicAuth


######################################################################
# Enter your admin email, token and baseurl without the /
######################################################################
user = 'email'
token = 'token'
baseurl = 'URL'
######################################################################

auth = HTTPBasicAuth(user, token)

csv_file = open('wproperties.csv', 'a', encoding="utf-8")
csv_file.write('T.ID,W. Name,P. Key,P. Value,P. ID')
csv_file.write('\n')

url = baseurl + '/rest/api/3/workflow/search'

headers = {
    'Accept': 'application/json'
}

query = {
    'isActive': 'true',
    'expand':  'transitions.properties,projects'
}

response = requests.request(
    'GET',
    url,
    headers=headers,
    params=query,
    auth=auth
).json()

w = response['total']
print(w)

i = 0

for i in range(w):
    wurl = baseurl + '/rest/api/3/workflow/search?maxResults=1&isActive=true&startAt=' + str(i)

    nr = requests.request(
        'GET',
        wurl,
        headers=headers,
        params=query,
        auth=auth
    ).json()

    wname = nr['values'][0]['id']['name']
    wtrans = len(nr['values'][0]['transitions'])

    for t in range(wtrans):
        tid = nr['values'][0]['transitions'][t]['id']

        turl = baseurl + '/rest/api/3/workflow/transitions/' + tid + '/properties'

        tquery = {
            'workflowName': wname
        }

        tp = requests.request(
            'GET',
            turl,
            headers=headers,
            params=tquery,
            auth=auth
        ).json()

        tlen = len(tp)

        for p in range(tlen):
            pkey = tp[p]['key']
            pvalue = tp[p]['value']
            pid = tp[p]['id']

            csv_file.write(f'{tid},{wname},{pkey},{pvalue},{pid}')
            csv_file.write("\n")

            print(wname, tid, pkey, pvalue, pid)

csv_file.close()
