import os
import tkinter as tk
from tkinter import filedialog, messagebox
import re


def select_entities_file():
    file_path = filedialog.askopenfilename(filetypes=[("XML Files", "*.xml")])
    if file_path:
        entities_entry.delete(0, tk.END)
        entities_entry.insert(0, file_path)


def select_export_descriptor_file():
    file_path = filedialog.askopenfilename(filetypes=[("Properties Files", "*.properties")])
    if file_path:
        export_descriptor_entry.delete(0, tk.END)
        export_descriptor_entry.insert(0, file_path)
        read_old_key(file_path)


def read_old_key(file_path):
    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith("spaceKey="):
                old_key = line.split('=')[1].strip()
                old_key_entry.config(state=tk.NORMAL)
                old_key_entry.delete(0, tk.END)
                old_key_entry.insert(0, old_key)
                old_key_entry.config(state='readonly')
                break


def update_files():
    entities_path = entities_entry.get()
    export_descriptor_path = export_descriptor_entry.get()
    new_key = new_key_entry.get().strip()

    if not entities_path or not export_descriptor_path or not new_key:
        messagebox.showerror("Error", "Please fill in all fields.")
        return

    old_key = old_key_entry.get().strip()
    old_key_l = old_key.lower()
    new_key_l = new_key.lower()

    # Update entities.xml file
    with open(entities_path, 'r', encoding='utf-8') as f:
        file_content = f.read()

    replacements = [
        (f"<property name=\"lowerDestinationSpaceKey\"><![CDATA[{old_key_l}]]></property>",
         f"<property name=\"lowerDestinationSpaceKey\"><![CDATA[{new_key_l}]]></property>"),
        (f"<property name=\"lowerKey\"><![CDATA[{old_key_l}]]></property>",
         f"<property name=\"lowerKey\"><![CDATA[{new_key_l}]]></property>"),
        (f"[{old_key}]", f"[{new_key}]"),
        (f"[{old_key_l}]", f"[{new_key_l}]"),
        (f"spaceKey={old_key}", f"spaceKey={new_key}"),
        (f"spaceKey={old_key_l}", f"spaceKey={new_key_l}"),
        (f"[{old_key}:", f"[{new_key}:"),
        (f"key={old_key}]", f"key={new_key}]"),
        (f"<spaceKey>{old_key}</spaceKey>", f"<spaceKey>{new_key}</spaceKey>"),
        (f"ri:space-key=\"{old_key}\"", f"ri:space-key=\"{new_key}\""),
        (f"ri:space-key={old_key}", f"ri:space-key={new_key}"),
        (f"<ac:parameter ac:name=\"spaces\">{old_key}</ac:parameter>",
         f"<ac:parameter ac:name=\"spaces\">{new_key}</ac:parameter>"),
        (f"<ac:parameter ac:name=\"spaceKey\">{old_key}</ac:parameter>",
         f"<ac:parameter ac:name=\"spaceKey\">{new_key}</ac:parameter>"),
        (f"<property name=\"key\"><![CDATA[{old_key}]]></property>",
         f"<property name=\"key\"><![CDATA[{new_key}]]></property>"),
        (f"<property name=\"context\"><![CDATA[{old_key}]]></property>",
         f"<property name=\"context\"><![CDATA[{new_key}]]></property>"),
        (f"<property name=\"destinationSpaceKey\"><![CDATA[{old_key}]]></property>",
         f"<property name=\"destinationSpaceKey\"><![CDATA[{new_key}]]></property>")
    ]

    after_replace = file_content
    for old, new in replacements:
        after_replace = after_replace.replace(old, new)

    entities_old_path = os.path.join(os.path.dirname(entities_path), 'entities_old.xml')
    entities_new_path = os.path.join(os.path.dirname(entities_path), 'entities.xml')

    os.rename(entities_path, entities_old_path)
    with open(entities_new_path, 'w', encoding='utf-8') as f:
        f.write(after_replace)

    # Update exportDescriptor.properties file
    with open(export_descriptor_path, 'r') as f:
        properties_content = f.read()

    properties_content = properties_content.replace(f"spaceKey={old_key}", f"spaceKey={new_key}")

    export_descriptor_old_path = os.path.join(os.path.dirname(export_descriptor_path), 'exportDescriptor_old.properties')
    export_descriptor_new_path = os.path.join(os.path.dirname(export_descriptor_path), 'exportDescriptor.properties')

    os.rename(export_descriptor_path, export_descriptor_old_path)
    with open(export_descriptor_new_path, 'w') as f:
        f.write(properties_content)

    messagebox.showinfo("Success", "Files have been updated successfully.")


def validate_new_key(new_key):
    # Check if new_key contains only ASCII letters and numbers
    if re.match("^[A-Za-z0-9]*$", new_key):
        return True
    return False


def on_validate_new_key(P):
    if validate_new_key(P):
        return True
    else:
        root.bell()  # Sound a bell to alert the user
        return False


# Create the main window
root = tk.Tk()
root.title("Confluence Space Key Updater")

# Register the validation command
vcmd = (root.register(on_validate_new_key), '%P')

# Create and place widgets
tk.Label(root, text="Entities.xml File:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
entities_entry = tk.Entry(root, width=50)
entities_entry.grid(row=0, column=1, padx=10, pady=5)
tk.Button(root, text="Browse...", command=select_entities_file).grid(row=0, column=2, padx=10, pady=5)

tk.Label(root, text="exportDescriptor.properties File:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
export_descriptor_entry = tk.Entry(root, width=50)
export_descriptor_entry.grid(row=1, column=1, padx=10, pady=5)
tk.Button(root, text="Browse...", command=select_export_descriptor_file).grid(row=1, column=2, padx=10, pady=5)

tk.Label(root, text="Old Space Key:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
old_key_entry = tk.Entry(root, width=50, state='readonly')
old_key_entry.grid(row=2, column=1, padx=10, pady=5)

tk.Label(root, text="New Space Key:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
new_key_entry = tk.Entry(root, width=50, validate='key', validatecommand=vcmd)
new_key_entry.grid(row=3, column=1, padx=10, pady=5)

tk.Button(root, text="Run", command=update_files).grid(row=4, column=0, columnspan=3, pady=10)

# Run the main loop
root.mainloop()
