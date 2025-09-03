import requests
from requests.auth import HTTPBasicAuth
import time

######################################################################
# Enter your admin email, token and baseurl without the /
######################################################################
user = ""
token = ""
baseurl = ""
######################################################################
######################################################################
# Enter the CSV file path (optional) and name where to save the data
csv_file = ''
######################################################################

start = time.time()

file = open(csv_file, 'a', encoding='utf-8')
file.write('Name,Space Key,Type')
file.write('\n')

s = requests.Session()

s.auth = HTTPBasicAuth(user, token)

s.headers.update({
    'Accept': 'application/json'
                  })

resp = s.get(baseurl + '/wiki/api/v2/spaces?limit=250&start=0').json()

resp_max = int(len(resp['results']))

print(resp_max)

i = 0

for i in range(resp_max):
    sp_url = s.get(baseurl + '/wiki/api/v2/spaces' + '?maxResults=1&startAt=' + str(i))
    file.write(f'{resp["results"][i]["name"]},{resp["results"][i]["key"]},{resp["results"][i]["type"]}')
    file.write("\n")
    print(resp['results'][i]['name'], ' - ', resp['results'][i]['key'], ' - ', resp['results'][i]['type'])
file.close()

print(time.time() - start, 'seconds')
