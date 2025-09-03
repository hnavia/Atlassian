import csv
import pandas as pd
from bs4 import BeautifulSoup
import os

######################################################################
# Uncomment to increase the CSV file size limit if needed in MB
######################################################################
size = 25
csv.field_size_limit(size * 1024 * 1024)
######################################################################
# Enter CSV path + name, plugin keywords and CSV delimiter
######################################################################
csv_file = r'D:\Accounts\Temp\even-more-workflows.csv'  # Active Workflow CSV Path
keywords_to_search = ['smartchecklist', 'tm4j', 'tempo-plugin', 'sla', 'jsu', 'jira-suite-utilities', 'clone-plus',
                      'jmwe', 'j-tricks', 'sqlfeed', 'mcf', 'structure', 'exalate', 'display-linked-issues',
                      'onenetwork', 'timepiece', 'export', 'drawio']  # Add more keywords if needed
delimiter = '\t'  # Choose the delimiter, TAB by default
######################################################################
######################################################################


def extract_data_from_xml_bs(xml_data, workflow_name, keywords):
    soup = BeautifulSoup(xml_data, 'xml')  # Use XML parser mode
    output = []

    for action in soup.find_all('action'):
        action_id = action.get('id')
        action_name = action.get('name')
        function_type = 'unknown-function'

        for keyword in keywords:
            for arg in action.find_all('arg', {'name': 'class.name'}):
                if arg.text and keyword in arg.text.lower():
                    if 'condition' in arg.text.lower():
                        function_type = 'condition'
                    elif 'validator' in arg.text.lower():
                        function_type = 'validator'
                    elif 'function' in arg.text.lower():
                        function_type = 'post-function'
                    transition_info = f"{action_name} ({action_id})"
                    output.append([workflow_name, transition_info, keyword, function_type])
    return output


results = []

with open(csv_file, 'r', encoding='utf-8') as file:
    reader = csv.reader(file, delimiter=delimiter)
    header = next(reader)  # Skip header
    for row_num, row in enumerate(reader, start=2):  # Row number for debugging
        if len(row) < 2:
            print(f"[WARNING] Invalid row {row_num}: {row}")
            continue
        workflow_name, xml_descriptor = row[0].strip(), row[1].strip()
        try:
            results.extend(extract_data_from_xml_bs(xml_descriptor, workflow_name, keywords_to_search))
        except Exception as e:
            print(f"[ERROR] Error processing workflow '{workflow_name}' in row {row_num}: {e}")

# Create DataFrame
df = pd.DataFrame(results, columns=['Workflow Name', 'Transition', 'Plugin', 'Function Type'])
df.drop_duplicates(inplace=True)

# Display results
print("\nOutput DataFrame:")
print(df)

# Save CSV in the same directory with "_parsed" suffix
base_dir = os.path.dirname(csv_file)
base_name = os.path.splitext(os.path.basename(csv_file))[0]
output_csv_file = os.path.join(base_dir, f"{base_name}_parsed.csv")

df.to_csv(output_csv_file, index=False)
print(f"\nCSV successfully generated at: {output_csv_file}")
