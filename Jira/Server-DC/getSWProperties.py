import requests
from requests.auth import HTTPBasicAuth
import time

######################################################################
# Enter your admin username, password and baseurl without the /
######################################################################
user = ''
pword = ''
baseurl = ''
######################################################################
######################################################################
# Set 'fullInstance' = True to get all the workflows properties
# Set 'fullInstance' = False to get specific workflows properties
fullInstance = True
######################################################################
######################################################################
# For Specific workflow properties, provide the name of the workflows
# Replace the below examples with the proper workflow names
wname = ['Workflow 1', 'Workflow 2', 'Workflow 3', 'etc']
######################################################################
######################################################################
# Specify the scan range for ID's - Default 1000
prange = ['1', '4', '11', '21', '31', '41', '51', '61', '71', '81', '91', '101', '111', '121', '131', '141', '151', '161', '171', '181', '301', '311', '711', '721', '731', '741', '751', '991', '1001', '1011', '1021', '1031', '1051', '1061']
######################################################################
######################################################################
# Enter the name of the CSV file where to save the properties
csv_file = 'properties.csv'
######################################################################

start = time.time()

file = open('properties.csv', 'a', encoding='utf-8')
file.write('T.ID,W. Name,P. Key,P. Value,P. ID')
file.write('\n')

s = requests.Session()

s.auth = HTTPBasicAuth(user, pword)

s.headers.update({
    'Accept': 'application/json',
})

if fullInstance:

    resp = s.get(baseurl + '/rest/api/2/workflow').json()

    wrange = int(len(resp))

    for i in range(wrange):
        w_name = resp[i]['name']
        print(resp[i]['name'])

        n = 0

        for n in prange:
            t_url = s.get(baseurl + '/rest/api/2/workflow/transitions/' + str(n) + '/properties?&workflowName=' + str(w_name)).json()
            print(t_url)

            t_len = int(len(t_url))
            p = 0

            for p in range(t_len):
                if t_len != 0:
                    try:
                        print(i, n, w_name, t_url[p]['key'], t_url[p]['value'], t_url[p]['id'])

                        tpkey = t_url[p]['key']
                        tpvalue = t_url[p]['value']
                        tpid = t_url[p]['id']

                        file.write(f'{n},{w_name},{tpkey},{tpvalue},{tpid}')
                        file.write('\n')

                    except KeyError:
                        continue

else:
    i = 0
    for i in wname:
        print(i)
        for n in range(prange):
            t_url = s.get(baseurl + '/rest/api/2/workflow/transitions/' + str(n) + '/properties?&workflowName=' + str(i)).json()
            print(t_url)

            t_len = int(len(t_url))

            for p in range(t_len):
                try:
                    if t_len != 0:
                        try:
                            print(p, n, wname, t_url[p]['key'], t_url[p]['value'], t_url[p]['id'])

                            tpkey = t_url[p]['key']
                            tpvalue = t_url[p]['value']
                            tpid = t_url[p]['id']

                            file.write(f'{n},{i},{tpkey},{tpvalue},{tpid}')
                            file.write('\n')

                        except KeyError:
                            continue
                except KeyError:
                    continue

file.close()

print(time.time() - start, 'seconds')
