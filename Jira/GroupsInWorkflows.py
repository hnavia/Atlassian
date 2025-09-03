import csv
import xml.etree.ElementTree as eT
import pandas as pd
import os
import re

######################################################################
# Uncomment to increase the size of the CSV file if needed in MB
######################################################################
size = 25
csv.field_size_limit(size * 1024 * 1024)
######################################################################
# Enter CSV path + name for workflows and groups
######################################################################
workflows_csv_file = r'D:\Clientes\Solera\SQL Outputs\Solera\Workflows\Active_Workflows.csv'
groups_csv_file = r'D:\Clientes\Solera\SQL Outputs\Solera\Groups\groups.csv'
workflows_delimiter = '\t'  # Tab delimiter for workflows file
groups_delimiter = ','  # Comma delimiter for groups file
######################################################################
######################################################################

def extract_data_from_xml(xml_data, workflow_name, groups):
    try:
        root = eT.fromstring(xml_data)
    except eT.ParseError as e:
        print(f"Error parsing XML for workflow '{workflow_name}': {e}")
        return []  # Skip this entry if XML is not well-formed

    output = []
    for action in root.findall('.//action'):
        action_id = action.get('id')
        action_name = action.get('name')

        for group in groups:
            group = group.strip()  # Remove any leading or trailing spaces
            group_lower = group.lower()  # Convert group name to lowercase for case-insensitive match

            # Create a pattern to exactly match the group name
            pattern = rf'\b{re.escape(group_lower)}\b'  # Word boundaries ensure it's an exact word, not part of another string

            for arg in action.findall('.//arg'):
                if arg.text is not None:
                    # Convert the text to lowercase for comparison
                    arg_text_lower = arg.text.lower()

                    # Check if the exact group name exists
                    if re.search(pattern, arg_text_lower):
                        # Verify that the group match is exact, not part of a larger string like "SMR - APU"
                        # Ensure it's not within another word
                        matched_groups = re.findall(pattern, arg_text_lower)

                        # Only append if the exact group name is found
                        if group_lower in matched_groups:
                            transition_info = f"{action_name} ({action_id})"
                            output.append([workflow_name, transition_info, group])
    return output

# Verify if the groups CSV file exists
if not os.path.exists(groups_csv_file):
    print(f"Groups file not found: {groups_csv_file}")
else:
    # Load groups from the CSV file
    groups = []
    with open(groups_csv_file, 'r', encoding='utf-8') as groups_file:
        groups_reader = csv.reader(groups_file, delimiter=groups_delimiter)  # Use comma delimiter for groups
        next(groups_reader)  # Skip the header row

        for row in groups_reader:
            if len(row) < 1:  # Ensure the row has at least 3 columns
                print(f"Skipping malformed group row: {row}")
                continue
            groups.append(row[0].strip())  # Use the third column

    if not groups:
        print("No valid groups found in the file.")
    else:
        results = []

        with open(workflows_csv_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=workflows_delimiter)  # Use tab delimiter for workflows
            next(reader)  # Skip the header row

            for row in reader:
                if len(row) < 2:  # Ensure there are at least 2 columns in the workflow CSV
                    print(f"Skipping malformed workflow row: {row}")
                    continue

                workflow_name = row[0].strip()  # Column 0: Workflow Name
                xml_descriptor = row[1].strip()  # Column 1: XML Descriptor
                results.extend(extract_data_from_xml(xml_descriptor, workflow_name, groups))

        # Create a DataFrame from the results
        df = pd.DataFrame(results, columns=['Workflow Name', 'Transition', 'Group'])

        # Drop duplicates if any
        df.drop_duplicates(inplace=True)

        # Print the DataFrame
        print("Output DataFrame:")
        print(df, flush=True)

        # Export the DataFrame to a new CSV file
        output_csv_file = r'D:\Clientes\Solera\SQL Outputs\Solera\Workflows\new_groups_5.csv'
        df.to_csv(output_csv_file, index=False)

        print("\nCSV file 'workflows_and_groups.csv' has been created successfully.")
