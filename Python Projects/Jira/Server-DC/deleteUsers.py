import os
import requests
import csv
import time
import concurrent.futures

######################################################################
# Enter your Personal Access Token and base URL without the last "/"
######################################################################
pat = ''
baseurl = 'http://10.131.21.30:8080/'  # Trailing slash "/" will be removed automatically
######################################################################
# Enter the path to the CSV file that contains the users to delete
input_csv_file = r''
######################################################################

# Automatically generate output CSV file name
input_dir = os.path.dirname(input_csv_file)  # Get directory of input file
input_filename = os.path.basename(input_csv_file)  # Get file name of input
output_filename = os.path.splitext(input_filename)[0] + '_results.csv'  # Append '_results' to base name
output_csv_file = os.path.join(input_dir, output_filename)  # Combine directory and new file name

baseurl = baseurl.rstrip('/')  # Ensure no trailing slash

# Function to delete user from Jira
def delete_user(session, user_id, username, user_key):
    url = f'{baseurl}/rest/api/2/user'
    params = {'key': user_key}  # You can also use 'username' if needed
    response = session.delete(url, params=params)

    if response.status_code == 204:
        return user_id, username, user_key, 'Deleted successfully'
    else:
        try:
            # Attempt to parse JSON error response
            error_message = response.json()
            error_details = error_message.get('errorMessages', []) + [f"{k}: {v}" for k, v in error_message.get('errors', {}).items()]
            error_text = "; ".join(error_details) if error_details else response.text
        except ValueError:
            # If response is not JSON, return raw text
            error_text = response.text

        return user_id, username, user_key, f"Error {response.status_code}: {error_text}"

# Function to read CSV file with user data
def read_csv(input_csv_file):
    users = []
    with open(input_csv_file, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip the header row if it exists
        for row in reader:
            user_id = row[0]  # Assuming 'id' is in the 1st column (index 0)
            username = row[1]  # Assuming 'username' is in the 2nd column (index 1)
            user_key = row[2]  # Assuming 'key' is in the 3rd column (index 2)
            users.append((user_id, username, user_key))
    return users

start = time.time()

# Open CSV to write results
with open(output_csv_file, 'w', encoding='utf-8', newline='') as file:
    writer = csv.writer(file, quoting=csv.QUOTE_ALL)

    # Write the header row for results CSV
    writer.writerow(['User ID', 'Username', 'User Key', 'Status'])

    # Start session and set up authorization header with PAT
    s = requests.Session()
    s.headers.update({
        'Accept': 'application/json',
        'Authorization': f'Bearer {pat}'  # Use the PAT for authentication
    })

    # Read user data (id, username, key) from CSV
    users_to_delete = read_csv(input_csv_file)

    # Parallelize user deletions using ThreadPoolExecutor for better performance
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for user_id, username, user_key in users_to_delete:
            futures.append(executor.submit(delete_user, s, user_id, username, user_key))

        # Process results as they come in
        for future in concurrent.futures.as_completed(futures):
            user_id, username, user_key, status = future.result()
            print(f"User {user_id}, {username}, {user_key}: {status}")

            # Write result to CSV
            writer.writerow([user_id, username, user_key, status])

print(f"Results saved to: {output_csv_file}")
print(f"Execution time: {time.time() - start} seconds")
