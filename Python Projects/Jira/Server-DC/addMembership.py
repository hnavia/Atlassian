import requests
import csv
import os
from datetime import datetime
import time

# Configuration
pat = ''  # Personal Access Token
baseurl = ''  # Update to your Jira instance base URL
input_csv_file = r''  # Input CSV with users and groups
uColumn = 0  # Enter the number of the UserName Column from the CSV
gColumn = 1  # Enter the number of the Group Column from the CSV

# Ensure no trailing slash in baseurl
baseurl = baseurl.rstrip('/')

# Automatically generate the log file name based on the input CSV file
input_dir = os.path.dirname(input_csv_file)  # Get directory of input file
input_filename = os.path.basename(input_csv_file)  # Get file name of input
log_filename = os.path.splitext(input_filename)[0] + '_results.csv'  # Append '_results' to base name
log_file = os.path.join(input_dir, log_filename)  # Combine directory and new file name

# API headers for PAT authentication
headers = {
    'Authorization': f'Bearer {pat}',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

# Prepare log file
if not os.path.exists(log_file):
    with open(log_file, 'w', encoding='utf8') as logfile:
        logfile.write('Time,User,Group,Status,Message\n')

# Cache for user existence checks
nonexistent_users = set()  # Track users that don't exist
checked_users = set()  # Track users already checked

# Helper functions
def user_exists(username):
    """Check if a user exists in Jira."""
    if username in checked_users:
        return True  # User already confirmed to exist
    response = requests.get(f'{baseurl}/rest/api/2/user', headers=headers, params={'username': username})
    if response.status_code == 200:
        checked_users.add(username)  # Add to cache of checked users
        return True
    nonexistent_users.add(username)  # Add to cache of nonexistent users
    return False


def group_exists(group_name):
    """Check if a group exists in Jira."""
    response = requests.get(f'{baseurl}/rest/api/2/group', headers=headers, params={'groupname': group_name})
    return response.status_code == 200


def create_group(group_name):
    """Create a group in Jira."""
    payload = {'name': group_name}
    response = requests.post(f'{baseurl}/rest/api/2/group', headers=headers, json=payload)
    return response.status_code == 201, response.text


def add_user_to_group(username, group_name):
    """Add a user to a group in Jira."""
    payload = {'name': username}
    response = requests.post(
        f'{baseurl}/rest/api/2/group/user',
        headers=headers,
        params={'groupname': group_name},
        json=payload
    )
    return response.status_code in [200, 201], response.text


# Process CSV
with open(input_csv_file, 'r') as file, open(log_file, 'a', encoding='utf8') as logfile:
    reader = csv.reader(file)
    header = next(reader)  # Skip header row if present
    total_users = sum(1 for _ in reader)
    file.seek(0)
    next(reader)  # Reset to first row after header
    print(f"Total users to process: {total_users}")

    for index, row in enumerate(reader, start=1):
        username = row[uColumn].strip()  # Username in column 2
        group_name = row[gColumn].strip()  # Group name in column 4

        if not username or not group_name:
            # Skip empty rows
            message = f"Row {index}: Skipped - Empty username or group name"
            logfile.write(f'{datetime.now()}, {username}, {group_name}, Skipped, Empty username or group name\n')
            print(message)
            continue

        print(f"Processing {index}/{total_users}: User '{username}' for group '{group_name}'")

        # Skip users already identified as non-existent
        if username in nonexistent_users:
            message = f"Row {index}: Skipped - User '{username}' does not exist (cached)"
            logfile.write(f'{datetime.now()}, {username}, {group_name}, Skipped, User does not exist (cached)\n')
            print(message)
            continue

        # Check if the user exists
        if not user_exists(username):
            message = f"Row {index}: Skipped - User '{username}' does not exist"
            logfile.write(f'{datetime.now()}, {username}, {group_name}, Skipped, User does not exist\n')
            print(message)
            continue

        # Check if the group exists, create if not
        if not group_exists(group_name):
            success, response_message = create_group(group_name)
            if not success:
                message = f"Row {index}: Failed - Group creation failed for '{group_name}'. Error: {response_message}"
                logfile.write(f'{datetime.now()}, {username}, {group_name}, Failed, {response_message}\n')
                print(message)
                continue

        # Add the user to the group
        success, response_message = add_user_to_group(username, group_name)

        if success:
            message = f"Row {index}: Success - User '{username}' added to group '{group_name}'"
            logfile.write(f'{datetime.now()}, {username}, {group_name}, Success, {message}\n')
            print(message)
        else:
            # Handle user already being a member of the group or other failure
            if "already a member of" in response_message:
                message = f"Row {index}: Skipped - User '{username}' is already a member of group '{group_name}'"
                logfile.write(f'{datetime.now()}, {username}, {group_name}, Skipped, User is already a member\n')
                print(message)
            else:
                message = f"Row {index}: Failed - User '{username}' addition to group '{group_name}' failed. Error: {response_message}"
                logfile.write(f'{datetime.now()}, {username}, {group_name}, Failed, {response_message}\n')
                print(message)

    print("Processing complete. Check the log file for details.")
