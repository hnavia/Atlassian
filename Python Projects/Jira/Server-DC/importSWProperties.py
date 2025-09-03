import requests
from requests.auth import HTTPBasicAuth
import json
import csv
import os
from datetime import datetime
import time

######################################################################
# Configuration: Set Authentication Method and Inputs
######################################################################
auth_type = "PAT"  # Options: "PAT" for Personal Access Token, "Basic" for Email & Password

# For PAT
pat = ''  # Replace with your PAT

# For Basic Auth
email = 'admin@example.com'  # Replace with your email
password = 'admin_password'  # Replace with your password

# Jira Base URL (Trailing slash "/" will be removed automatically)
baseurl = ''

# Path to the input CSV file with workflow properties
input_csv_file = r'D:\Clientes\Solera\DryRun\SQL Outputs\cleaned_properties-29-05-2025.csv'
######################################################################

# Remove trailing slash from base URL if present
baseurl = baseurl.rstrip('/')

# Generate log file path based on the input CSV file
log_file = os.path.splitext(input_csv_file)[0] + '_result.csv'

# Start timer for execution
start = time.time()

# Create a session for reusing connections
s = requests.Session()

# Set authentication based on the selected method
if auth_type == "Basic":
    s.auth = HTTPBasicAuth(email, password)
    print("Using Basic Authentication...")
elif auth_type == "PAT":
    s.headers.update({
        'Authorization': f'Bearer {pat}'
    })
    print("Using Personal Access Token (PAT)...")
else:
    print("Invalid authentication type. Exiting.")
    exit()

# Common headers
s.headers.update({
    'Accept': 'application/json',
    'Content-Type': 'application/json'
})

# Open the input CSV file
file = open(input_csv_file, 'r')
reader = csv.reader(file)
next(reader)  # Skip the header line

# Open the log file to track results
logfile = open(log_file, 'a', encoding='utf8')
logfile.write('Time,Workflow Name,Transition ID,Code,Message\n')

# Process each row in the CSV
for line in reader:
    # Line elements:
    # line[0] = Transition ID
    # line[1] = Workflow Name
    # line[2] = Property Key
    # line[3] = Property Value

    # API query parameters
    query_params = {
        'key': line[2],  # Property key
        'workflowName': line[1],  # Workflow name
        'workflowMode': 'draft'  # Use "live" for published workflows
    }

    # Payload to define the property value
    payload = json.dumps({
        'value': line[3]  # Property value
    })

    # API endpoint URL
    url = f"{baseurl}/rest/api/2/workflow/transitions/{line[0]}/properties"

    # Make the PUT request
    resp = s.put(url, params=query_params, data=payload)

    # Logging success or error
    if resp.status_code in (200, 201):  # Success codes
        logfile.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{line[1]},{line[0]},{resp.status_code},Successful\n")
        print(f"Success: Workflow={line[1]}, Transition={line[0]}, Status={resp.status_code}")
    else:  # Errors
        try:
            error_message = resp.json().get('errors', {}).get('key', 'Unknown error')
        except Exception:
            error_message = resp.text  # Fallback to raw response text

        logfile.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{line[1]},{line[0]},{resp.status_code},{error_message}\n")
        print(f"Error: Workflow={line[1]}, Transition={line[0]}, Status={resp.status_code}, Message={error_message}")

# Close files and print completion message
file.close()
logfile.close()
print(f"Script completed in {round(time.time() - start, 2)} seconds.")
print(f"Log file saved at: {log_file}")
