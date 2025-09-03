import requests
from requests.auth import HTTPBasicAuth
import csv
import time
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
import webbrowser


# Function to show the "About" screen
def show_about():
    about_window = tk.Toplevel(root)
    about_window.title("About")

    # Information about the tool with placeholder for the email
    about_info = (
        "Jira Cloud Workflows & Plugins Analyzer\n"
        "Version: 1.0\n\n"
        "Created by: Hugo Navia\n\n"
        "Contact:"
    )

    # Display the about info without the email
    tk.Label(about_window, text=about_info, padx=20, pady=10).pack()

    # Email label for clickable email address
    email_label = tk.Label(about_window, text="hugo.navia@servicerocket.com", fg="blue", cursor="hand2")
    email_label.pack(pady=5)

    # Bind the click event to open the email client
    def open_email(event):
        webbrowser.open("mailto:hugo.navia@servicerocket.com")

    email_label.bind("<Button-1>", open_email)

    # Tool description below the contact information
    tool_description = (
        "This tool analyzes workflows in Jira Cloud and looks for specific plugins\n"
        "or functions used in workflow transitions based on user-defined keywords."
    )

    tk.Label(about_window, text=tool_description, padx=20, pady=10).pack()

    # Button to close the about window
    tk.Button(about_window, text="Close", command=about_window.destroy).pack(pady=10)


# Function to show the "How To" screen
def show_how_to():
    howto_window = tk.Toplevel(root)
    howto_window.title("How To Use the Tool")

    # ScrolledText widget for scrollable instructions
    instruction_text = scrolledtext.ScrolledText(howto_window, wrap=tk.WORD, width=50, height=15, padx=10, pady=10)
    instruction_text.pack(fill=tk.BOTH, expand=True)

    # Step-by-step instructions
    instructions = (
        "Step-by-Step Instructions to Use Jira Cloud Workflows & Plugins Analyzer:\n\n"
        "1. Enter your Jira Cloud user credentials (User and Token).\n"
        "   - You can generate an API token in your Jira Cloud account settings.\n\n"
        "2. Enter the base URL for your Jira Cloud instance.\n"
        "   - Example: https://your-domain.atlassian.net\n\n"
        "3. Specify the keywords (comma-separated) you want to search for in the workflows.\n"
        "   - Example: 'jmwe, groovy, jsu'\n\n"
        "4. Click the 'Start' button to begin the analysis.\n\n"
        "5. The tool will fetch workflows and analyze the transitions to detect the specified plugins.\n"
        "6. Progress will be displayed on the progress bar during the analysis.\n"
        "7. A CSV file named 'Workflows&Plugins.csv' will be generated containing the results.\n\n"
        "Make sure all fields are filled out before starting the script."
    )

    # Insert instructions into the text area and disable editing
    instruction_text.insert(tk.END, instructions)
    instruction_text.config(state=tk.DISABLED)

    # Close button
    tk.Button(howto_window, text="Close", command=howto_window.destroy).pack(pady=10)


# Tkinter GUI setup
root = tk.Tk()
root.title("Jira Cloud Workflows & Plugins Analyzer")

# Adding menu
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

# Add "How To" and "About" directly as menu items
menu_bar.add_command(label="How To", command=show_how_to)
menu_bar.add_command(label="About", command=show_about)

# Main script function
def start_script():
    user = entry_user.get().strip()
    token = entry_token.get().strip()
    baseurl = entry_url.get().strip().rstrip('/')
    keywords_to_search = [keyword.strip() for keyword in entry_keywords.get().strip().split(',')]

    if not user or not token or not baseurl or not keywords_to_search:
        messagebox.showerror("Input Error", "All fields must be filled out.")
        return

    csv_file = 'Workflows&Plugins.csv'
    progress_bar['value'] = 0
    progress_label.config(text="Starting...")

    # Start the script
    run_script(user, token, baseurl, keywords_to_search, csv_file)


# Script execution function
def run_script(user, token, baseurl, keywords_to_search, csv_file):
    try:
        start = time.time()

        with open(csv_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Workflow Name', 'Transition', 'Plugin', 'Function Type'])

            s = requests.Session()
            s.auth = HTTPBasicAuth(user, token)
            s.headers.update({'Accept': 'application/json'})

            start_at = 0
            max_results = 50
            more_pages = True
            results = []

            while more_pages:
                response = s.get(
                    f'{baseurl}/rest/api/3/workflow/search?expand=transitions.rules,statuses,operations&isActive=true&startAt={start_at}&maxResults={max_results}')
                if response.status_code != 200:
                    messagebox.showerror("API Error", f"Error fetching data: {response.status_code}\n{response.text}")
                    return
                else:
                    data = response.json()
                    workflows = data.get('values', [])
                    total = data.get('total', 0)
                    progress_bar['maximum'] = total

                    def extract_data_from_json(workflow, keywords):
                        output = []
                        workflow_name = workflow['id']['name']
                        for transition in workflow.get('transitions', []):
                            transition_id = transition['id']
                            transition_name = transition['name']
                            transition_info = f"{transition_name} ({transition_id})"
                            function_type = 'unknown-function'

                            for rule_type in ['validators', 'postFunctions']:
                                for rule in transition.get('rules', {}).get(rule_type, []):
                                    for keyword in keywords:
                                        if keyword in rule['type'].lower():
                                            if 'validator' in rule['type'].lower():
                                                function_type = 'validator'
                                            elif 'condition' in rule['type'].lower():
                                                function_type = 'condition'
                                            elif 'function' in rule['type'].lower():
                                                function_type = 'post-function'
                                            output.append([workflow_name, transition_info, keyword, function_type])

                        return output

                    for workflow in workflows:
                        results.extend(extract_data_from_json(workflow, keywords_to_search))
                        progress_bar['value'] += 1
                        root.update_idletasks()

                    start_at += max_results
                    more_pages = not data.get('isLast', True)

            writer.writerows(results)

            if not results:
                messagebox.showinfo("Result", "No matching plugins found in the workflows.")
            else:
                messagebox.showinfo("Success", f"Number of rows written to CSV: {len(results)}")

        progress_label.config(text="Completed")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")


# Input fields
tk.Label(root, text="User:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
entry_user = tk.Entry(root, width=40)
entry_user.grid(row=0, column=1, padx=10, pady=5)

tk.Label(root, text="Token:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
entry_token = tk.Entry(root, show="*", width=40)
entry_token.grid(row=1, column=1, padx=10, pady=5)

tk.Label(root, text="Base URL:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
entry_url = tk.Entry(root, width=40)
entry_url.grid(row=2, column=1, padx=10, pady=5)

tk.Label(root, text="Keywords (comma separated):").grid(row=3, column=0, padx=10, pady=5, sticky="e")
entry_keywords = tk.Entry(root, width=40)
entry_keywords.grid(row=3, column=1, padx=10, pady=5)

# Progress bar and label
progress_label = tk.Label(root, text="Idle")
progress_label.grid(row=4, column=0, padx=10, pady=5, sticky="w")
progress_bar = ttk.Progressbar(root, length=300, mode='determinate')
progress_bar.grid(row=4, column=1, padx=10, pady=5)

# Start button
start_button = tk.Button(root, text="Start", command=start_script)
start_button.grid(row=5, column=0, columnspan=2, pady=10)

root.mainloop()
