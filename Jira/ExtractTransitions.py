import csv
import xml.etree.ElementTree as eT
import pandas as pd
import os

######################################################################
# Uncomment to increase the size of the CSV file if needed in MB
######################################################################
size = 25
csv.field_size_limit(size * 1024 * 1024)
######################################################################
# Enter CSV path + name and delimiter
######################################################################
csv_file = r'D:\Clientes\Solera\DryRun\SQL Outputs\Solera_All_Workflows.csv'
delimiter = '\t'  # Tab delimiter (change to ',' for comma, etc.)
######################################################################
######################################################################

def extract_transition_info(xml_data):
    """Extract transition information from XML data."""
    root = eT.fromstring(xml_data)
    transitions = []

    for action in root.findall('.//action'):
        action_id = action.get('id')
        action_name = action.get('name')
        transitions.append((action_name, action_id))

    return transitions


results = []

# Process the input CSV file
with open(csv_file, 'r', encoding='utf-8') as file:
    reader = csv.reader(file, delimiter=delimiter)
    next(reader)  # Skip the header row

    for row in reader:
        workflow_name = row[0].strip()  # Column 0: Workflow Name
        xml_descriptor = row[1].strip()  # Column 1: XML Descriptor
        transitions = extract_transition_info(xml_descriptor)
        results.extend([(workflow_name,) + transition for transition in transitions])

# Create a DataFrame from the results
df = pd.DataFrame(results, columns=['Workflow Name', 'Transition Name', 'Transition ID'])

# Drop duplicates if any
df.drop_duplicates(inplace=True)

# Automatically generate the output file name
csv_output_file = os.path.splitext(csv_file)[0] + '_transitions.csv'

# Save the DataFrame to the output CSV file
df.to_csv(csv_output_file, index=False)

# Print the final output
print(df)
print(f"CSV file '{csv_output_file}' has been created successfully.")
