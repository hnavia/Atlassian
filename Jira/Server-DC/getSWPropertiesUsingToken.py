import requests
import time
import csv
import os
import concurrent.futures

######################################################################
# Enter your Personal Access Token and base URL without the last /
######################################################################
pat = ''
baseurl = ''
######################################################################
# Enter the path to the CSV file that contains the workflows and IDs
input_csv_file = r'D:\Clientes\Solera\DryRun\SQL Outputs\Solera_All_Workflows_transitions-29-05-2025.csv'
######################################################################

# Remove trailing slash from base URL if present
baseurl = baseurl.rstrip('/')

# Automatically generate the output file name in the same directory
output_csv_file = os.path.join(
    os.path.dirname(input_csv_file),
    "properties_result.csv"
)

def fetch_transition_properties(session, workflow_name, n):
    t_url = f'{baseurl}/rest/api/2/workflow/transitions/{n}/properties?&workflowName={workflow_name}'
    t_url_response = session.get(t_url)
    if t_url_response.status_code == 200:
        return t_url_response.json(), n, workflow_name
    else:
        print(f"Failed to retrieve properties for transition {n}. Status Code: {t_url_response.status_code}")
        return None, n, workflow_name

def read_csv(input_csv_file):
    workflows_and_pids = {}
    with open(input_csv_file, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip the header row if it exists
        for row in reader:
            workflow_name = row[0]  # Assuming Workflow Name is in Column 0
            pid = row[2]  # Assuming PID is in Column 2
            if workflow_name in workflows_and_pids:
                workflows_and_pids[workflow_name].append(int(pid))
            else:
                workflows_and_pids[workflow_name] = [int(pid)]
    return workflows_and_pids

start = time.time()

with open(output_csv_file, 'w', encoding='utf-8', newline='') as file:
    writer = csv.writer(file, quoting=csv.QUOTE_ALL)
    writer.writerow(['Transition ID', 'Workflow Name', 'Property Key', 'Property Value', 'Property ID'])

    s = requests.Session()
    s.headers.update({
        'Accept': 'application/json',
        'Authorization': f'Bearer {pat}'  # Use the PAT for authentication
    })

    # Read workflows and pids from CSV
    workflows_and_pids = read_csv(input_csv_file)

    # Parallelize HTTP requests for each workflow and transition ID
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for workflow_name, pids in workflows_and_pids.items():
            for n in pids:
                futures.append(executor.submit(fetch_transition_properties, s, workflow_name, n))

        for future in concurrent.futures.as_completed(futures):
            t_url_json, n, workflow_name = future.result()
            if t_url_json:
                for prop in t_url_json:
                    try:
                        tpkey = prop['key']
                        tpvalue = prop['value']
                        tpid = prop['id']
                        print(f"{n}, {workflow_name}, {tpkey}, {tpvalue}, {tpid}")

                        # Escape double quotes in data by doubling them
                        workflow_name = workflow_name.replace('"', '""')
                        tpkey = tpkey.replace('"', '""')
                        tpvalue = tpvalue.replace('"', '""')
                        tpid = tpid.replace('"', '""')

                        writer.writerow([n, workflow_name, tpkey, tpvalue, tpid])
                    except KeyError:
                        continue

print(f"Execution time: {time.time() - start} seconds")
print(f"CSV file '{output_csv_file}' has been created successfully.")
