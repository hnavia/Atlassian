import requests
from requests.auth import HTTPBasicAuth
import csv
from datetime import datetime
import time

# Configuration Section
######################################################################
# Enter your admin email, token, and base URL without the trailing slash
######################################################################
user = 'EMAIL'
token = 'TOKEN'
baseurl = 'URL'
######################################################################

# Enter the CSV file path and name containing the user data
csv_file = 'userlist.csv'

# Enter the group IDs from which users should be removed
groups = ['groupID_1', 'groupID_2', ..., 'groupID_N']

# Enter the path (optional) and name of the log file
log = 'log_groupmembership.csv'
######################################################################

# Start Time
start = time.time()

# Open the CSV file containing the user data
with open(csv_file, 'r') as file:
    reader = csv.reader(file)
    next(reader)  # Skip the header row

    # Open log file
    with open(log, 'a', encoding='utf8') as logfile:
        logfile.write('Time,User,Group,Code,Message\n')

        # Create a session with basic authentication
        s = requests.Session()
        s.auth = HTTPBasicAuth(user, token)

        # Loop through each line in the CSV file
        for line in reader:
            # Loop through each group
            for g in groups:
                # Define the query parameters for the API request
                query = {
                    'groupId': g,
                    'accountId': line[0]
                }

                try:
                    # Send a DELETE request to remove the user from the group
                    resp = s.delete(baseurl + '/rest/api/2/group/user', params=query)
                    resp.raise_for_status()  # Raise exception for HTTP errors

                    final_error_message = 'Successful'
                except requests.exceptions.HTTPError as e:
                    final_error_message = f'HTTP error: {e}'
                except Exception as e:
                    final_error_message = f'Error: {e}'

                # Log the result of the request
                logfile.write(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")},{line[2]},{"3ed5554a-1497-43a9-9392-3adffede255e"},{resp.status_code},{final_error_message}\n')
                print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")},{line[2]},{"3ed5554a-1497-43a9-9392-3adffede255e"},{resp.status_code},{final_error_message}')

# End Time
print(time.time() - start, 'seconds')
