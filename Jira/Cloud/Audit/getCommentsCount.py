import requests
from requests.auth import HTTPBasicAuth
import time

######################################################################
# Enter your admin email, token and baseurl without the /
######################################################################
user = 'email'
token = 'token'
baseurl = 'baseurl'
######################################################################
######################################################################
# Enter the CSV file path (optional) and name where to save the data
csv_file = 'commentscount.csv'
######################################################################

start = time.time()

file = open(csv_file, 'a', encoding='utf-8')
file.write('Project Key,Issue Key,Total Comments #')
file.write('\n')

s = requests.Session()

s.auth = HTTPBasicAuth(user, token)

s.headers.update({
    'Accept': 'application/json'
                  })

resp = s.get(baseurl + '/rest/api/3/project/search').json()

i = 0

for i in range(resp['total']):
    url = s.get(baseurl + '/rest/api/3/project/search' + '?maxResults=1' + '&startAt=' + str(i))

    p = url.json()['values'][0]['key']

    iurl = s.get(baseurl + '/rest/api/3/search?jql=project=' + p).json()

    print(iurl['total'])

    for c in range(iurl['total']):
        kurl = s.get(baseurl + '/rest/api/3/search?jql=project=' + p + '&maxResults=1&startAt=' + str(c)).json()
        issue_key = kurl['issues'][0]['key']

        curl = s.get(baseurl + '/rest/api/3/issue/' + issue_key + '/comment').json()

        ccount = curl['total']

        file.write(f'{p},{issue_key},{ccount}')
        file.write('\n')
        print(f'{p},{issue_key},{ccount}')

file.close()

print(time.time() - start, 'seconds')
