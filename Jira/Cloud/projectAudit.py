import requests
import csv

######################################################################
# Enter your Jira Cloud credentials here
######################################################################
user_email = ""  # Replace with your Jira email
api_token = ""  # Replace with your Jira API token
jira_url = ""  # Replace with your Jira instance URL
######################################################################

def get_jira_projects(user_email, api_token, jira_url):
    """
    Retrieves the list of projects and their project keys from Jira Cloud.

    Args:
        user_email (str): The Jira user's email.
        api_token (str): The Jira API token.
        jira_url (str): Your Jira instance URL (e.g., https://your-domain.atlassian.net).

    Returns:
        list: A list of dictionaries, where each dictionary represents a project with its name and key.
              Returns None on error.
    """
    url = f"{jira_url}/rest/api/3/project"
    headers = {
        "Accept": "application/json"
    }
    auth = (user_email, api_token)

    try:
        response = requests.get(url, headers=headers, auth=auth)
        response.raise_for_status()  # Raise an exception for HTTP error codes
        projects = response.json()
        return [{"name": project["name"], "key": project["key"]} for project in projects]
    except requests.exceptions.RequestException as e:
        print(f"Error getting Jira projects: {e}")
        return None

def save_projects_to_csv(projects, filename="all_jira_projects.csv"):
    """
    Saves the list of projects to a CSV file.

    Args:
        projects (list): The list of project dictionaries.
        filename (str): The name of the CSV file to save.
    """
    if projects:
        try:
            with open(filename, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = ["name", "key"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                writer.writerows(projects)

            print(f"The list of projects has been saved to '{filename}'.")
        except IOError as e:
            print(f"Error saving the CSV file: {e}")

if __name__ == "__main__":
    projects = get_jira_projects(user_email, api_token, jira_url)
    save_projects_to_csv(projects)