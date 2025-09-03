import os
import requests
import csv
import json
import logging
import time
import concurrent.futures

######################################################################
# Enter your Personal Access Token and base URL
######################################################################
pat = ''  # Personal Access Token
baseurl = ''  # Trailing slash "/" will be removed automatically
######################################################################
# Enter the path to the CSV file that contains the users to rename
input_csv_file = r'D:\Clientes\Solera\Jira\Redcap\User_Cleanup\allUsers.csv'
######################################################################

# Automatically generate output CSV file name
input_dir = os.path.dirname(input_csv_file)  # Get directory of input file
input_filename = os.path.basename(input_csv_file)  # Get file name of input
output_filename = os.path.splitext(input_filename)[0] + '_results.csv'  # Append '_results' to base name
output_csv_file = os.path.join(input_dir, output_filename)  # Combine directory and new file name

# Configure logging
logging.basicConfig(
    filename='rename_users.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

baseurl = baseurl.rstrip('/')  # Ensure no trailing slash


# Function to rename a user
def rename_user(session, user_id, username, email_address):
    url = f'{baseurl}/rest/api/2/user?username={username}'
    new_name = email_address.lower()
    payload = json.dumps({"name": new_name})

    try:
        response = session.put(url, headers=session.headers, data=payload)
        if response.status_code == 204:
            logger.info(f"User {user_id} ({username}) renamed to {new_name} successfully.")
            return user_id, username, email_address, response.status_code, "Renamed successfully"
        else:
            try:
                # Parse JSON response for detailed error
                error_message = response.json()
                error_details = (
                        error_message.get('errorMessages', []) +
                        [f"{k}: {v}" for k, v in error_message.get('errors', {}).items()]
                )
                error_text = "; ".join(error_details) if error_details else response.text
            except ValueError:
                # Handle non-JSON responses
                error_text = response.text

            status_code = response.status_code
            logger.error(
                f"Failed to rename user {user_id} ({username}): HTTP {status_code} - {error_text}"
            )
            return user_id, username, email_address, status_code, f"Error: {error_text}"
    except Exception as e:
        logger.exception(f"An unexpected error occurred while renaming user {user_id} ({username}): {str(e)}")
        return user_id, username, email_address, "N/A", f"Exception: {str(e)}"


# Function to read user data from CSV
def read_csv(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header row
            return [(row[0], row[1], row[2]) for row in reader]  # Columns: ID, Username, Email
    except FileNotFoundError:
        logger.error(f"Input CSV file not found: {file_path}")
        raise
    except Exception as e:
        logger.exception(f"An error occurred while reading the CSV file: {str(e)}")
        raise


# Main script
def main():
    start_time = time.time()

    try:
        # Read users from the input CSV
        users_to_rename = read_csv(input_csv_file)

        # Open CSV to write results
        with open(output_csv_file, 'w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file, quoting=csv.QUOTE_ALL)
            # Updated CSV Header
            writer.writerow(['User ID', 'Username', 'Email Address', 'HTTP Status', 'Status'])

            # Start session for API requests
            session = requests.Session()
            session.headers.update({
                'Accept': 'application/json',
                'Authorization': f'Bearer {pat}',
                'Content-Type': 'application/json'
            })

            # Use ThreadPoolExecutor for parallel requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [
                    executor.submit(rename_user, session, user_id, username, email_address)
                    for user_id, username, email_address in users_to_rename
                ]

                # Process results
                for future in concurrent.futures.as_completed(futures):
                    user_id, username, email_address, http_status, status = future.result()
                    console_output = f"User {user_id}, {username}, {email_address}: HTTP {http_status} - {status}"
                    print(console_output)
                    writer.writerow([user_id, username, email_address, http_status, status])

        elapsed_time = time.time() - start_time
        logger.info(f"Execution completed in {elapsed_time:.2f} seconds")
        print(f"Results saved to: {output_csv_file}")
        print(f"Execution completed in {elapsed_time:.2f} seconds")

    except Exception as e:
        logger.exception(f"An unexpected error occurred during the main execution: {str(e)}")
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
