import csv
import xml.etree.ElementTree as eT
import pandas as pd
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

######################################################################
# Uncomment to increase the size of the CSV file if needed in MB
######################################################################
size = 25
csv.field_size_limit(size * 1024 * 1024)
######################################################################


# Function to extract data from XML
def extract_data_from_xml(xml_data, workflow_name, keywords):
    root = eT.fromstring(xml_data)
    output = []

    for action in root.findall('.//action'):
        action_id = action.get('id')
        action_name = action.get('name')
        function_type = 'unknown-function'

        for keyword in keywords:
            for arg in action.findall('.//arg[@name="class.name"]'):
                if arg.text is not None and keyword in arg.text.lower():
                    if 'condition' in arg.text.lower():
                        function_type = 'condition'
                    elif 'validator' in arg.text.lower():
                        function_type = 'validator'
                    elif 'function' in arg.text.lower():
                        function_type = 'post-function'
                    transition_info = f"{action_name} ({action_id})"
                    output.append([workflow_name, transition_info, keyword, function_type])

    return output


# Function to open the file dialog and get the CSV file
def get_csv_file():
    csv_file_path = filedialog.askopenfilename(title="Select CSV File", filetypes=[("CSV Files", "*.csv")])
    if csv_file_path:
        entry_csv_file.delete(0, tk.END)  # Clear previous entry
        entry_csv_file.insert(0, csv_file_path)  # Insert selected file path


# Function to run the analysis
def run_analysis():
    csv_file = entry_csv_file.get().strip()
    keywords_to_search = [keyword.strip() for keyword in entry_keywords.get().strip().split(',')]

    if not csv_file or not keywords_to_search:
        messagebox.showerror("Input Error", "Please select a CSV file and enter keywords.")
        return

    results = []

    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter='\t')  # Use tab delimiter
        next(reader)  # Skip the header row

        for row in reader:
            workflow_name, xml_descriptor = row
            xml_descriptor = xml_descriptor.strip()  # Strip whitespace
            for keyword in keywords_to_search:
                results.extend(extract_data_from_xml(xml_descriptor, workflow_name, [keyword]))

    # Create a DataFrame from the results
    df = pd.DataFrame(results, columns=['Workflow Name', 'Transition', 'Plugin', 'Function Type'])
    df.drop_duplicates(inplace=True)

    # Print the DataFrame
    print("Output DataFrame:")
    print(df, flush=True)

    # Export the DataFrame to a new CSV file
    output_csv_file = filedialog.asksaveasfilename(defaultextension=".csv", title="Save Output CSV File", filetypes=[("CSV Files", "*.csv")])
    if output_csv_file:
        df.to_csv(output_csv_file, index=False)
        messagebox.showinfo("Success", f"CSV file '{output_csv_file}' has been created successfully.")


# Function to show the "About" screen
def show_about():
    about_window = tk.Toplevel(root)
    about_window.title("About")

    # Information about the tool with placeholder for the email
    about_info = (
        "Jira Workflows & Plugins Analyzer\n"
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
        "This tool analyzes XML data from Jira workflows\n"
        "to look for specific plugins or functions based on user-defined keywords."
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
        "Step-by-Step Instructions to Use Jira Workflows & Plugins Analyzer:\n\n"
        "1. Click 'Select CSV File' to choose the CSV file containing workflows and XML data.\n"
        "2. Enter the keywords you want to search for, separated by commas.\n"
        "   - Example: 'groovy, jmwe, label, smart, xray'\n\n"
        "3. Click the 'Analyze' button to begin the analysis.\n\n"
        "4. The tool will process the data and generate a summary of the findings.\n"
        "5. You will be prompted to save the output CSV file containing the results.\n\n"
        "Make sure all fields are filled out before starting the analysis."
    )

    # Insert instructions into the text area and disable editing
    instruction_text.insert(tk.END, instructions)
    instruction_text.config(state=tk.DISABLED)

    # Close button
    tk.Button(howto_window, text="Close", command=howto_window.destroy).pack(pady=10)


# Tkinter GUI setup
root = tk.Tk()
root.title("Jira Workflows & Plugins Analyzer")

# Input fields
tk.Label(root, text="CSV File:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
entry_csv_file = tk.Entry(root, width=40)
entry_csv_file.grid(row=0, column=1, padx=10, pady=5)
tk.Button(root, text="Select CSV File", command=get_csv_file).grid(row=0, column=2, padx=10, pady=5)

tk.Label(root, text="Keywords (comma separated):").grid(row=1, column=0, padx=10, pady=5, sticky="e")
entry_keywords = tk.Entry(root, width=40)
entry_keywords.grid(row=1, column=1, padx=10, pady=5)

# Analyze button
analyze_button = tk.Button(root, text="Analyze", command=run_analysis)
analyze_button.grid(row=2, column=0, columnspan=3, pady=10)

# Adding menu
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

# Add "How To" and "About" directly as menu items
menu_bar.add_command(label="How To", command=show_how_to)
menu_bar.add_command(label="About", command=show_about)

# Start the Tkinter main loop
root.mainloop()
