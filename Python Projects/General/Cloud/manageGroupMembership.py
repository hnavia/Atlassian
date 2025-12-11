import requests
import csv
import time
from datetime import datetime

# ================================================================
# CONFIGURATION
# ================================================================
api_key = 'YOUR_API_KEY'
org_id = 'YOUR_ORG_ID'
directory_id = 'YOUR_DIRECTORY_ID'

csv_file = r'C:\path\to\file.csv'

# Options: 'add' or 'remove'
action = 'remove'

# Dry run: True = simulate without making changes
dry_run = False

# Log file auto-generated from CSV name
log_file = csv_file.replace('.csv', '') + '_log.csv'

# ------------------------------------------------
# CSV COLUMN INDEXES (update these if your CSV changes)
# ------------------------------------------------
COL_GROUP_ID = 0
COL_GROUP_NAME = 1
COL_USER_ID = 2
COL_USER_NAME = 3
COL_EMAIL = 4
# ================================================================


# ================================================================
# HELPER FUNCTIONS
# ================================================================
def color(text, code):
    '''Add console color for readability.'''
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'reset': '\033[0m'
    }
    return f"{colors.get(code, '')}{text}{colors['reset']}"


def log_and_print(writer, data):
    '''Write to log file and show formatted console output.'''

    status = data['status_code']
    message = data['message']

    # Select console color
    if status in (200, 204, 'DRY'):
        c = 'green'
    elif status in (400, 401, 403, 404, 409):
        c = 'yellow'
    else:
        c = 'red'

    # Console output
    print(color(
        f"{data['timestamp']} | {data['email']} | {data['group_name']} | "
        f"{status} | {message}",
        c
    ))

    # Log CSV entry
    writer.writerow([
        data['timestamp'],
        data['user_id'],
        data['user_name'],
        data['email'],
        data['group_name'],
        data['group_id'],
        status,
        message
    ])


# ================================================================
# API FUNCTIONS
# ================================================================
def remove_from_group(session, org_id, directory_id, group_id, account_id):
    '''Remove user from a group.'''
    url = (
        f'https://api.atlassian.com/admin/v2/orgs/{org_id}/directories/'
        f'{directory_id}/groups/{group_id}/memberships/{account_id}'
    )

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json'
    }

    for attempt in range(5):
        resp = session.delete(url, headers=headers)

        if resp.status_code == 204:
            return resp.status_code, 'Successful'

        if resp.status_code == 429:  # rate limit
            time.sleep(2 ** attempt)
            continue

        try:
            return resp.status_code, resp.json()
        except:
            return resp.status_code, resp.text

    return resp.status_code, 'Failed after retries'


def add_to_group(session, org_id, directory_id, group_id, account_id):
    '''Add user to a group.'''
    url = (
        f'https://api.atlassian.com/admin/v2/orgs/{org_id}/directories/'
        f'{directory_id}/groups/{group_id}/memberships'
    )

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json'
    }

    payload = {'accountId': account_id}

    for attempt in range(5):
        resp = session.post(url, headers=headers, json=payload)

        if resp.status_code == 204:
            return resp.status_code, 'Successful'

        if resp.status_code == 429:  # rate limit
            time.sleep(2 ** attempt)
            continue

        try:
            return resp.status_code, resp.json()
        except:
            return resp.status_code, resp.text

    return resp.status_code, 'Failed after retries'


# ================================================================
# MAIN EXECUTION
# ================================================================
start = time.time()

print('\n=======================================')
print('         STARTING GROUP SCRIPT')
print('=======================================\n')

session = requests.Session()

stats = {
    'processed': 0,
    'successful': 0,
    'errors': 0,
    'rate_limited': 0
}

# Open log file
with open(log_file, 'w', encoding='utf8', newline='') as lf:
    writer = csv.writer(lf)
    writer.writerow([
        'timestamp', 'user_id', 'user_name', 'email',
        'group_name', 'group_id', 'status_code', 'message'
    ])

    # Read CSV
    with open(csv_file, 'r', encoding='utf8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header

        for row in reader:
            stats['processed'] += 1

            # Extract values based on column indexes
            group_id = row[COL_GROUP_ID]
            group_name = row[COL_GROUP_NAME]
            user_id = row[COL_USER_ID]
            user_name = row[COL_USER_NAME]
            email = row[COL_EMAIL]

            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # --------------------------------------------------------
            # DRY RUN (no changes sent)
            # --------------------------------------------------------
            if dry_run:
                log_and_print(writer, {
                    'timestamp': timestamp,
                    'user_id': user_id,
                    'user_name': user_name,
                    'email': email,
                    'group_name': group_name,
                    'group_id': group_id,
                    'status_code': 'DRY',
                    'message': f'Simulated {action}'
                })
                continue

            # --------------------------------------------------------
            # REAL ACTION
            # --------------------------------------------------------
            if action == 'remove':
                status_code, message = remove_from_group(
                    session, org_id, directory_id, group_id, user_id
                )

            elif action == 'add':
                status_code, message = add_to_group(
                    session, org_id, directory_id, group_id, user_id
                )

            else:
                raise ValueError("Invalid action. Use 'add' or 'remove'.")

            # Update counters
            if status_code == 204:
                stats['successful'] += 1
            elif status_code == 429:
                stats['rate_limited'] += 1
                stats['errors'] += 1
            else:
                stats['errors'] += 1

            # Log result
            log_and_print(writer, {
                'timestamp': timestamp,
                'user_id': user_id,
                'user_name': user_name,
                'email': email,
                'group_name': group_name,
                'group_id': group_id,
                'status_code': status_code,
                'message': message
            })

# ================================================================
# SUMMARY
# ================================================================
print('\n=======================================')
print('                SUMMARY')
print('=======================================\n')

print(f"Total processed : {stats['processed']}")
print(color(f"Successful      : {stats['successful']}", 'green'))
print(color(f"Errors          : {stats['errors']}", 'red'))
print(color(f"Rate limited    : {stats['rate_limited']}", 'yellow'))

print(f'\nCompleted in {time.time() - start:.2f} seconds.')
print(f'Log saved to:\n{log_file}\n')

print('=======================================')
print('                 DONE')
print('=======================================\n')
