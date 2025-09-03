import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# --- Configuration ---
JIRA_URL = ""
USERNAME = ""
PASSWORD = ""
WORKFLOW_CSV = r"D:\Clientes\Solera\DryRun\SQL Outputs\cleaned_properties-29-05-2025.csv"
CSV_COLUMN_INDEX = 1  # Change this index to select the correct workflow name column

# Remove trailing slash from base URL if present
JIRA_URL = JIRA_URL.rstrip('/')

# --- Load allowed workflow names from CSV ---
def load_workflow_names(csv_file, column_index):
    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        return [row[column_index].strip() for row in reader if len(row) > column_index and row[column_index].strip()]

allowed_workflows = load_workflow_names(WORKFLOW_CSV, CSV_COLUMN_INDEX)

print(f"📄 Loaded {len(allowed_workflows)} workflow(s) from CSV:")
for name in allowed_workflows:
    print(f"   • {name}")

# --- Set up Chrome ---
options = webdriver.ChromeOptions()
options.add_argument("--no-first-run")
options.add_argument("--no-default-browser-check")

driver = webdriver.Chrome(options=options)

try:
    # Step 1: Login
    print("🔄 Navigating to login page...")
    driver.get(f"{JIRA_URL}/login.jsp")

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "login-form-username")))
    driver.find_element(By.ID, "login-form-username").send_keys(USERNAME)
    driver.find_element(By.ID, "login-form-password").send_keys(PASSWORD)

    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "login-form-submit"))).click()
    print("✅ Login submitted.")
    time.sleep(5)

    # Step 2: Go to Workflows page
    print("🔄 Navigating to Workflows admin page...")
    driver.get(f"{JIRA_URL}/secure/admin/workflows/ListWorkflows.jspa")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "aui-page-panel")))
    time.sleep(3)

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    # Step 3: Find and filter workflows by data-workflow-name
    print("🔍 Scanning for workflows to match CSV list...")

    workflow_rows = driver.find_elements(By.XPATH, "//tr[@data-workflow-name]")
    workflow_edit_links = []

    for row in workflow_rows:
        wf_name = row.get_attribute("data-workflow-name").strip()
        if wf_name in allowed_workflows:
            try:
                edit_link = row.find_element(By.XPATH, ".//a[@data-operation='edit']")
                href = edit_link.get_attribute("href")
                if href:
                    full_url = href if href.startswith("http") else JIRA_URL + "/" + href.lstrip("/")
                    print(f"✅ Matched and added: {wf_name}")
                    workflow_edit_links.append(full_url)
            except Exception as e:
                print(f"⚠️ Could not find Edit link for {wf_name}: {e}")
        else:
            print(f"⛔ Skipped: {wf_name} (not in CSV)")

    # Step 4: Open matching Edit links in new tabs
    for i, url in enumerate(workflow_edit_links, start=1):
        print(f"🆕 Opening Edit tab {i}: {url}")
        driver.execute_script(f"window.open('{url}', '_blank');")
        time.sleep(1)

    print("🎉 Selected Edit pages opened in new tabs.")

    # Step 5: Wait for manual inspection before proceeding
    input("⏸ Press Enter to publish all workflows...")

    # Step 6: Loop through tabs and publish workflows
    print("🚀 Publishing all workflows...")
    main_window = driver.current_window_handle
    all_tabs = driver.window_handles

    for i, handle in enumerate(all_tabs[1:], start=1):  # skip main tab
        driver.switch_to.window(handle)
        print(f"🖱️ Switching to tab {i}...")

        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "publish-draft")))
            time.sleep(2)

            publish_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "publish-draft"))
            )
            publish_button.click()
            print(f"✅ Clicked 'Publish Draft' in tab {i}.")
            time.sleep(3)

            # Select "No"
            no_label = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "label[for='publish-workflow-false']"))
            )
            no_label.click()
            print(f"🔘 Selected 'No' for saving a copy.")

            time.sleep(1)

            # Click final Publish button
            final_publish_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "publish-workflow-submit"))
            )
            final_publish_button.click()
            print(f"🚀 Final 'Publish' clicked in tab {i}.")

            time.sleep(2)

        except Exception as e:
            print(f"⚠️ Could not complete publish in tab {i}: {e}")

    print("✅ All selected workflows published.")
    input("⏸ Press Enter to close the browser...")

except Exception as e:
    print(f"❌ Error: {e}")

finally:
    driver.quit()
    print("ℹ️ Script finished.")
