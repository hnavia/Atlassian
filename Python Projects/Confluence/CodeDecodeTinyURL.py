import base64
import csv

# Set your base URL, input/output file paths and action
new_url = 'https://page.com/pages/viewpage.action?pageId='
rest_new_url = 'https://page.com/rest/api/content?pageId='
csv_file = ''  # Replace with the actual path to your input file
output_file = ''      # Replace with the desired path for the output CSV file
createTinyURL = False

file_r = open(csv_file, 'r')
reader = csv.reader(file_r)
next(reader)  # so we skip the first line

file_w = open(output_file, 'a', encoding='utf-8')
file_w.write('Original TinyURL,TinyURL ID,Original URL,Original URL ID,Rest URL')
file_w.write('\n')

for line in reader:

    tiny = line[1]

    if createTinyURL == True:
        def page_id_to_tiny(page_id):
            return base64.b64encode((page_id).to_bytes(4, byteorder='little')).decode().replace('/', '-').replace('+', '_').rstrip('A=')

        file_w.write(f'{line[0]},{tiny_to_page_id(tiny)},{new_url + str(tiny)},{str(tiny)}')
        file_w.write("\n")

    else:
        def tiny_to_page_id(tiny):
            return int.from_bytes(base64.b64decode(tiny.ljust(8, 'A').replace('_', '+').replace('-', '/').encode()), byteorder='little')

        file_w.write(f'{line[0]},{tiny},{new_url + str(tiny_to_page_id(tiny))},{str(tiny_to_page_id(tiny))},{rest_new_url + str(tiny_to_page_id(tiny))}')
        file_w.write("\n")

        print(line[0], tiny, new_url + str(tiny_to_page_id(tiny)), tiny_to_page_id(tiny))


