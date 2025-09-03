import requests
from requests.auth import HTTPBasicAuth
import csv
import time
import os

######################################################################
# Enter your admin email, token and baseurl without the trailing /
######################################################################
user = ''
token = ''
baseurl = ''
baseurl = baseurl.rstrip('/')  # Ensure no trailing slash
######################################################################
# Input CSV file with emails (first column, first row is a header)
######################################################################
input_csv = r'D:\Clientes\Solera\Jira\Migration\Account Custom Field\users.csv'
######################################################################

# Automatically create output file path
input_dir = os.path.dirname(os.path.abspath(input_csv))
input_base = os.path.splitext(os.path.basename(input_csv))[0]
output_csv = os.path.join(input_dir, f'{input_base}_results.csv')

start = time.time()

emails = []
with open(input_csv, 'r', encoding='utf-8') as infile:
    reader = csv.reader(infile)
    next(reader)  # Skip first row (header like "Account Lead")
    for row in reader:
        if row and row[0].strip():
            emails.append(row[0].strip())

# Open output CSV file
with open(output_csv, 'w', encoding='utf-8', newline='') as outfile:
    writer = csv.writer(outfile)
    writer.writerow(['Username', 'ID'])  # Fixed headers for output

    s = requests.Session()
    s.auth = HTTPBasicAuth(user, token)
    s.headers.update({
        "Accept": "application/json"
    })

    for email in emails:
        response = s.get(f"{baseurl}/rest/api/3/user/search", params={"query": email})

        if response.status_code == 200:
            users = response.json()
            if users:  # If a user is found, write to CSV
                account_id = users[0].get("accountId", "")
                writer.writerow([email, account_id])
                print(f"{email} -> {account_id}")
            else:  # No user found
                writer.writerow([email, "NOT_FOUND"])
                print(f"{email} -> NOT_FOUND")
        else:
            print(f"Error for {email}: {response.status_code} - {response.text}")

print(f"\nExported to: {output_csv}")
print(f"Time taken: {time.time() - start:.2f} seconds")
