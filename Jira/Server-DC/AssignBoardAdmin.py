import requests
from requests.auth import HTTPBasicAuth
import json
import time

######################################################################
# Configuration: Choose authentication method
# Set auth_method to "basic" for Basic Auth or "pat" for Personal Access Token
######################################################################
auth_method = "pat"  # Change to "basic" if using username & password

# Credentials for Basic Auth
user = 'USERNAME'
pword = 'PASSWORD'

# Personal Access Token
pat = ''

# Base URL
baseurl = 'https://jiratest.jda.com/'
######################################################################
######################################################################
# Enter the Jira User Key for the new Board Admin
# Get the Jira User Key using this API in the URL: /rest/api/2/user?username=userName
boardAdmin = 'JIRAUSER87257'
# Enter the Boards ID's separated by commas
boardID = [6618]
######################################################################

# Ensure no trailing slash in baseurl
baseurl = baseurl.rstrip('/')

start = time.time()

s = requests.Session()

# Set authentication based on the chosen method
if auth_method == "basic":
    s.auth = HTTPBasicAuth(user, pword)
    s.headers.update({
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    })
elif auth_method == "pat":
    s.headers.update({
        'Authorization': f'Bearer {pat}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    })
else:
    raise ValueError("Invalid authentication method. Choose 'basic' or 'pat'.")

# Process board IDs
for n in boardID:
    payload = json.dumps({
        "id": n,
        "boardAdmins": {
            "userKeys": [
                boardAdmin
            ],
            "groupKeys": []
        }})

    resp = s.put(baseurl + '/rest/greenhopper/1.0/rapidviewconfig/boardadmins/', data=payload)

    print(resp)

print(time.time() - start, 'seconds')
