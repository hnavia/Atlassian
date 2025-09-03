import requests
import json
import csv

# INSERT "USER", "TOKEN", "BASE_URL" HERE
USER = ""
TOKEN = ""
BASE_URL = ""

with open('att_per_page.csv', 'w', encoding="utf-8", newline='') as pagecsvfile, open('att_per_space.csv', 'w', encoding="utf-8", newline='') as spacecsvfile:
    perPageWriter = csv.writer(pagecsvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    perSpaceWriter = csv.writer(spacecsvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    perPageWriter.writerow(['pageid', 'attachment_size(byte)'])
    perSpaceWriter.writerow(['space_name', 'space_key', 'attachment_size(byte)'])

    headers = {
        "Accept": "application/json"
    }

    response = requests.request(
        "GET",
        BASE_URL + "/wiki/rest/api/space?next=true&limit=200",
        headers=headers,
        auth=(USER, TOKEN)
    )

    try:
        response_data = json.loads(response.text)
        space_key_results = response_data.get("results", [])
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        print(f"Response content: {response.text}")
        space_key_results = []

    site_attachment_volume = 0

    # Get all space keys
    for space in space_key_results:
        space_attachment_volume = 0
        # Get related page IDs from space keys
        response = requests.request(
            "GET",
            BASE_URL + "/wiki/rest/api/space/" + space["key"] + "/content",
            headers=headers,
            auth=(USER, TOKEN)
        )

        try:
            response_data = json.loads(response.text)
            page_results = response_data.get("page", {}).get("results", [])
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            print(f"Response content: {response.text}")
            page_results = []

        for page in page_results:
            page_attachment_volume = 0
            # Get attachments from each page
            response = requests.request(
                "GET",
                BASE_URL + "/wiki/rest/api/content/" + page["id"] + "/child/attachment",
                headers=headers,
                auth=(USER, TOKEN)
            )
            try:
                response_data = json.loads(response.text)
                attachment_results = response_data.get("results", [])
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                print(f"Response content: {response.text}")
                attachment_results = []

            for attachment in attachment_results:
                page_attachment_volume += int(attachment["extensions"]["fileSize"])
                print("      " + "Attachment Name: " + json.dumps(attachment["title"]) + ", " + json.dumps(
                    attachment["extensions"]["fileSize"]) + " bytes")

            space_attachment_volume += page_attachment_volume
            print("      -->" + "PAGE TOTAL: " + str(page_attachment_volume))

            # Write to CSV
            perPageWriter.writerow([page["id"], str(page_attachment_volume)])

        print("\n         " + space["name"] + " (" + space["key"] + ")" + " SPACE TOTAL: " + str(space_attachment_volume) + " bytes")
        print("----------")

        # Write to CSV
        perSpaceWriter.writerow([space["name"], space["key"], str(space_attachment_volume)])
