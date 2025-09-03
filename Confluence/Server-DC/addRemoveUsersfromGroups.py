import requests
import csv
import time
from datetime import datetime
import os

######################################################################
# Configuration
######################################################################

# Confluence base URL (no trailing slash)
baseurl = ''

# Personal Access Token (PAT)
pat = ''

# Action: set to 'add' to add users to groups, or 'remove' to remove users
action = 'remove'  # options: 'add' or 'remove'

# CSV file containing user/group data
csv_file = r''

# CSV column index configuration (0-based index)
# Adjust these according to your CSV structure
user_id_col = 0       # Not used in API, but available for logging
username_col = 1      # Column containing the Confluence username
groupname_col = 2     # Column containing the group name

# Enable/disable bypass mode
# If True, no API calls will be made. The script will log "Bypassed".
bypass_mode = False
######################################################################

start = time.time()

# Ensure no trailing slash in baseurl
baseurl = baseurl.rstrip('/')

# Auto-generate log file path in the same folder as the CSV
csv_dir = os.path.dirname(os.path.abspath(csv_file))
csv_name = os.path.splitext(os.path.basename(csv_file))[0]
log_file = os.path.join(csv_dir, f'{csv_name}_log.csv')

# Open log file
with open(log_file, 'a', encoding='utf8') as logfile:
    logfile.write('Time,Action,UserId,UserName,GroupName,StatusCode,Message\n')

    # Setup requests session with PAT
    session = requests.Session()
    session.headers.update({
        'Authorization': f'Bearer {pat}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    })

    # Read CSV
    with open(csv_file, 'r', encoding='utf8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row

        for line in reader:
            user_id = line[user_id_col].strip()
            username = line[username_col].strip()
            groupname = line[groupname_col].strip()

            if bypass_mode:
                status_code = 'N/A'
                message = 'Bypassed'
            else:
                # Build URL for API request
                url = f'{baseurl}/rest/api/user/{username}/group/{groupname}'

                # Decide method based on action
                if action == 'add':
                    resp = session.put(url)
                elif action == 'remove':
                    resp = session.delete(url)
                else:
                    raise ValueError('Invalid action. Use "add" or "remove".')

                # Determine result message
                status_code = resp.status_code
                if status_code == 204:
                    message = 'Success'
                else:
                    try:
                        message = resp.json()
                    except Exception:
                        message = resp.text

            # Write log entry
            log_entry = (
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},"
                f'{action},{user_id},{username},{groupname},'
                f'{status_code},{message}'
            )
            logfile.write(log_entry + '\n')

            # Print to console
            print(log_entry)

print(time.time() - start, 'seconds')
