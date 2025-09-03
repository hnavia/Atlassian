import requests
import csv
import os
from datetime import datetime

# Configuration
pat = 'TOKEN'  # Replace with your Personal Access Token
baseurl = 'http://localhost:8090/'  # Replace with your Confluence instance base URL
input_csv_file = r'D:\PATH\TO\FILE\FILE.csv'  # Path to the input CSV file
space_key_column = 2  # The column index of the Space Key in your CSV file (zero-based)

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

# Payload to revoke permissions
payload = [
    {"targetType": "space", "operationKey": "read"},
    {"targetType": "space", "operationKey": "administer"},
    {"targetType": "space", "operationKey": "export"},
    {"targetType": "space", "operationKey": "restrict"},
    {"targetType": "space", "operationKey": "delete_own"},
    {"targetType": "space", "operationKey": "delete_mail"},
    {"targetType": "page", "operationKey": "create"},
    {"targetType": "page", "operationKey": "delete"},
    {"targetType": "blogpost", "operationKey": "create"},
    {"targetType": "blogpost", "operationKey": "delete"},
    {"targetType": "comment", "operationKey": "create"},
    {"targetType": "comment", "operationKey": "delete"},
    {"targetType": "attachment", "operationKey": "create"},
    {"targetType": "attachment", "operationKey": "delete"}
]

# Prepare log file
if not os.path.exists(log_file):
    with open(log_file, 'w', encoding='utf8') as logfile:
        logfile.write('Time,Space Key,Status,Message\n')

# Process the CSV file
with open(input_csv_file, 'r') as file, open(log_file, 'a', encoding='utf8') as logfile:
    reader = csv.reader(file)
    header = next(reader, None)  # Skip the header row if present
    space_keys = [row[space_key_column].strip() for row in reader if row]

    print(f"Total spaces to process: {len(space_keys)}")

    for index, space_key in enumerate(space_keys, start=1):
        print(f"Processing {index}/{len(space_keys)}: Revoking anonymous permissions for space '{space_key}'")

        # Construct the API URL
        url = f"{baseurl}/rest/api/space/{space_key}/permissions/anonymous/revoke"

        try:
            response = requests.put(url, headers=headers, json=payload)
            if response.status_code == 204:
                message = f"Row {index}: Success - Anonymous permissions revoked for space '{space_key}'"
                logfile.write(f'{datetime.now()}, {space_key}, Success, {message}\n')
                print(message)
            else:
                # Log failure with detailed error message
                error_message = response.json().get("message", "No detailed error message available.")
                message = f"Row {index}: Failed - Error: {error_message}"
                logfile.write(f'{datetime.now()}, {space_key}, Failed, {error_message}\n')
                print(message)
        except requests.exceptions.RequestException as e:
            # Handle network or request-related exceptions
            message = f"Row {index}: Failed - Network error: {str(e)}"
            logfile.write(f'{datetime.now()}, {space_key}, Failed, {str(e)}\n')
            print(message)

    print("Processing complete. Check the log file for details.")
