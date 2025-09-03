import requests
from requests.auth import HTTPBasicAuth
import csv
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

######################################################################
# Enter your admin email, token and baseurl without the /
######################################################################
user = 'UserName'
pword = 'password'
baseurl = 'baseurl'
######################################################################
######################################################################
# Enter the CSV file path (optional) and name where to save the data
csv_file = ''
######################################################################

# List of macros to search for
macro_list = ['composition-setup', 'cloak', 'toggle-cloak', 'deck', 'card']

start = time.time()

s = requests.Session()
s.auth = HTTPBasicAuth(user, pword)

# Function to fetch all results with pagination
def fetch_all_results(macro):
    all_results = []
    start = 0
    limit = 500
    while True:
        response = s.get(baseurl + '/rest/api/content/search', params={'cql': 'macro="' + macro + '"', 'start': start, 'limit': limit})
        response.raise_for_status()
        data = response.json()
        all_results.extend(data.get('results', []))
        if '_links' in data and 'next' in data['_links']:
            start += limit
        else:
            break
    return all_results

# Function to process each page data
def process_page_data(m, page_data):
    pagejson_response = s.get(baseurl + '/rest/api/content/' + str(page_data['id']))
    pagejson_response.raise_for_status()
    pagejson = pagejson_response.json()

    creator = pagejson["history"]["createdBy"].get("username", pagejson["history"]["createdBy"].get("displayName", ""))
    page_info = [
        m,
        pagejson["space"]["key"],
        pagejson["title"],
        creator,
        pagejson["history"]["createdDate"],
        pagejson["version"]["by"]["username"],
        pagejson["version"]["when"],
        baseurl + pagejson["_links"]["webui"]
    ]
    return page_info

# Open CSV file
with open(csv_file, 'w', newline='', encoding='utf8') as file:
    writer = csv.writer(file)
    writer.writerow(['Macro Name', 'Space Key', 'Page Title', 'Creator', 'Created Date', 'Last Modified by', 'Last Modified Date', 'Page URL'])

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for m in macro_list:
            all_results = fetch_all_results(m)
            print(f'Total results for {m}: {len(all_results)}')

            for page_data in all_results:
                futures.append(executor.submit(process_page_data, m, page_data))

        for future in as_completed(futures):
            try:
                page_info = future.result()
                writer.writerow(page_info)
            except Exception as e:
                print(f'Error processing page: {e}')

print(time.time() - start, 'seconds')
