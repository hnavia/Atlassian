import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup
import csv
import time
from datetime import datetime

######################################################################
# Enter your admin email, token and baseurl without the /
######################################################################
user = 'UserName'
pword = 'password'
baseurl = 'baseurl'
######################################################################
######################################################################
# Enter the CSV file path (optional) and name where to save the data
csv_file = 'UserMacros.csv'
######################################################################

start = time.time()

s = requests.session()
s.auth = HTTPBasicAuth(user, pword)

um_url = s.get(baseurl + '/admin/usermacros.action')
usermacro = BeautifulSoup(um_url.text, 'html.parser')
result = usermacro.find('table', id="user-macros-admin")

# Check if the result is None
if result is None:
    print("Error: 'user-macros-admin' table not found.")
    exit()

# Extract macro names
macro_list = []
for row in result.find_all('tr')[1:]:  # Exclude header row
    strong_tag = row.find('strong')
    if strong_tag:
        macro_name = strong_tag.get_text(strip=True)
        macro_list.append(macro_name)

print(macro_list)  # Debug: Print macro list to check if it's empty

# Function to fetch all results with pagination
def fetch_all_results(macro):
    all_results = []
    start = 0
    limit = 500
    while True:
        murl_response = s.get(baseurl + '/rest/api/content/search', params={'cql': 'macro="' + macro + '"', 'start': start, 'limit': limit})
        murl_response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
        try:
            murl = murl_response.json()
        except ValueError:
            print(f"Error: Invalid JSON response for macro '{macro}'")
            break  # Stop processing this macro
        all_results.extend(murl.get('results', []))
        if '_links' in murl and 'next' in murl['_links']:
            start += limit
        else:
            break
    return all_results

# Open CSV file
with open(csv_file, 'w', newline='', encoding='utf8') as file:
    writer = csv.writer(file)
    writer.writerow(['Macro Name', 'Space Key', 'Page Title', 'Creator', 'Created Date', 'Last Modified by', 'Last Modified Date', 'Page URL'])

    for m in macro_list:
        try:
            all_results = fetch_all_results(m)
            print(f'Total results for {m}: {len(all_results)}')  # Debug: Print total results

            for page_data in all_results:
                pagejson_response = s.get(baseurl + '/rest/api/content/' + str(page_data['id']))
                pagejson_response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes

                try:
                    pagejson = pagejson_response.json()
                    creator = pagejson["history"]["createdBy"].get("username", pagejson["history"]["createdBy"].get("displayName", ""))
                    created_date = datetime.strptime(pagejson["history"]["createdDate"], '%Y-%m-%dT%H:%M:%S.%f%z').strftime('%Y-%m-%d')
                    last_modified_date = datetime.strptime(pagejson["version"]["when"], '%Y-%m-%dT%H:%M:%S.%f%z').strftime('%Y-%m-%d')

                    print('===============================================\n')
                    print('Macro Name: ' + m)
                    print('Page Title: ' + pagejson["title"] + '\nSpaceKey: ' + pagejson["space"]["key"] + '\nCreator: ' + creator)
                    print('Created Date: ' + created_date)
                    print('Last Modified by: ' + pagejson["version"]["by"]["username"])
                    print('Last Modified Date: ' + last_modified_date)
                    print('Page URL: ' + baseurl + pagejson["_links"]["webui"])
                    print('\n\n===============================================\n')

                    writer.writerow([
                        m,
                        pagejson["space"]["key"],
                        pagejson["title"],
                        creator,
                        created_date,
                        pagejson["version"]["by"]["username"],
                        last_modified_date,
                        baseurl + pagejson["_links"]["webui"]
                    ])
                except KeyError as e:
                    print(f'Error processing page {page_data["id"]}: {e}')
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error occurred: {err}")

print(time.time() - start, 'seconds')
