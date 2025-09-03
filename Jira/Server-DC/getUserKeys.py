import requests
import csv
import time
import concurrent.futures

######################################################################
# Enter your Personal Access Token and base URL without the last /
######################################################################
pat = ''
baseurl = ''
######################################################################
# Enter the path to the CSV file that contains UserID and Username
input_csv_file = r'D:\Clientes\Solera\Jira\Scripts\deleteUsers\users_to_lookup.csv'  # Update with your input file path
######################################################################
# Enter the path and name of the CSV file to save the results
output_csv_file = r'D:\Clientes\Solera\Jira\Scripts\deleteUsers\user_keys.csv'  # Update with your desired output file path
######################################################################

# Function to fetch user key from Jira
def fetch_user_key(session, user_id, username):
    url = f'{baseurl}/rest/api/2/user'
    params = {'username': username}
    response = session.get(url, params=params)

    if response.status_code == 200:
        user_data = response.json()
        user_key = user_data.get('key', 'Key not found')
        return user_id, username, user_key
    elif response.status_code == 404:
        return user_id, username, 'User not found'
    elif response.status_code == 401:
        return user_id, username, 'Unauthorized - Check credentials'
    elif response.status_code == 403:
        return user_id, username, 'Forbidden - Check permissions'
    else:
        return user_id, username, f'Error {response.status_code}: {response.text}'

# Function to read CSV file with user data
def read_csv(input_csv_file):
    users = []
    with open(input_csv_file, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip the header row if it exists
        for row in reader:
            user_id = row[0]  # Assuming 'UserID' is in the 1st column (index 0)
            username = row[1]  # Assuming 'Username' is in the 2nd column (index 1)
            users.append((user_id, username))
    return users

start = time.time()

# Open CSV to write results
with open(output_csv_file, 'w', encoding='utf-8', newline='') as file:
    writer = csv.writer(file, quoting=csv.QUOTE_ALL)

    # Write the header row for results CSV
    writer.writerow(['UserID', 'Username', 'User Key'])

    # Start session and set up authorization header with PAT
    s = requests.Session()
    s.headers.update({
        'Accept': 'application/json',
        'Authorization': f'Bearer {pat}'  # Use the PAT for authentication
    })

    # Read user data (id, username) from CSV
    users_to_lookup = read_csv(input_csv_file)

    # Parallelize user lookups using ThreadPoolExecutor for better performance
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for user_id, username in users_to_lookup:
            futures.append(executor.submit(fetch_user_key, s, user_id, username))

        # Process results as they come in
        for future in concurrent.futures.as_completed(futures):
            user_id, username, user_key = future.result()
            print(f"User {user_id}, {username}: {user_key}")

            # Write result to CSV
            writer.writerow([user_id, username, user_key])

print(f"Execution time: {time.time() - start} seconds")
