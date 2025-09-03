import re
import csv

# Set your base URL and input/output file paths
base_url = ""
input_file_path = ""  # Replace with the actual path to your input file
output_file_path = ""      # Replace with the desired path for the output CSV file

def extract_urls(file_path, base_url):
    url_pattern = re.compile(f'<a href="{re.escape(base_url)}([a-zA-Z0-9_-]+)">')

    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    urls = url_pattern.findall(content)
    return urls

def write_to_csv(urls, output_file):
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Original URL', 'Code'])
        for url in urls:
            csv_writer.writerow([base_url + url, url])

# Extract URLs from the text file
urls = extract_urls(input_file_path, base_url)

# Write URLs to CSV
write_to_csv(urls, output_file_path)