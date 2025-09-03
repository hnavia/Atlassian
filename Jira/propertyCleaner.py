import csv
import os

# Specify your search values
search_values = {'10400', '10402', '10401', '10500', '10501', '1', '10201', '10200', '5', '10000'}

# Function to process a cell and filter the values
def process_cell(cell_value):
    if cell_value == '' or cell_value == '-1':  # Skip empty or -1 cells
        return None
    values = set(cell_value.split(','))
    matched_values = values.intersection(search_values)  # Keep only matching values
    # Skip the row if all values in the cell are in search_values
    if matched_values == values:
        return None
    # Return only matched values, or None if no match is found
    return ','.join(matched_values) if matched_values else None

# Input CSV file path
input_csv_file = r'D:\Clientes\Solera\Jira\Scripts\workflowFix\faulted_properties.csv'

# Automatically generate the output file name
output_csv_file = os.path.splitext(input_csv_file)[0] + '_cleaned.csv'

# Process the CSV
with open(input_csv_file, 'r', encoding='utf-8') as infile, open(output_csv_file, 'w', encoding='utf-8', newline='') as outfile:
    reader = csv.reader(infile)
    writer = csv.writer(outfile)

    # Write the header row
    headers = next(reader)
    writer.writerow(headers)

    # Process rows
    for row in reader:
        property_value = row[3]  # Column index 3: "Property Value"
        if property_value.strip() == '':  # Skip rows where Property Value is empty
            continue
        cleaned_value = process_cell(property_value)
        if cleaned_value is not None:  # Only write rows with non-skipped values
            row[3] = cleaned_value
            writer.writerow(row)

print(f"Filtered data has been saved to: {output_csv_file}")
