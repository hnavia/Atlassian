import csv
import sys
import requests
import datetime

# ======================================================================
# CONFIGURATION SECTION
# ======================================================================

org_id = 'ORG_ID'
api_key = 'YOUR_API_KEY'
directory_id = 'DIRECTORY_ID'
csv_file = r'C:\path\to\your\file.csv'

# ------------------------------------------------
# CSV COLUMN INDEXES (update these if your CSV changes)
# ------------------------------------------------
COL_ACCOUNT_ID = 0
COL_EMAIL      = 1
COL_ACTION     = 2
# ------------------------------------------------

# Log file
log_file = csv_file.replace('.csv', '') + '_log.csv'

# Global dry-run (applies to remove, suspend, restore)
dry_run = False

# ======================================================================
# INTERNAL SETUP
# ======================================================================

headers = {
    'Authorization': f'Bearer {api_key}',
    'Accept': 'application/json'
}

# Create log file with headers
with open(log_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['timestamp', 'accountId', 'email', 'action', 'error_code', 'status'])


# ======================================================================
# LOGGING
# ======================================================================

def log_action(account_id, email, action_type, error_code, status):
    with open(log_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.datetime.now().isoformat(),
            account_id,
            email,
            action_type,
            error_code,
            status
        ])


# ======================================================================
# CONFIRMATION PROMPT (only for REMOVE)
# ======================================================================

def confirm_remove():
    print('============================================================')
    print(' WARNING')
    print('------------------------------------------------------------')
    print(' This script will REMOVE USER ACCESS from the organization.')
    print(' This action is DESTRUCTIVE and cannot be undone.')
    print(' It will send DELETE requests for each accountId marked as "remove".')
    print('============================================================\n')

    user_input = input('Type YES / yes / Y / y to proceed: ').strip().lower()

    if user_input not in ['yes', 'y']:
        print('\nExecution cancelled. Confirmation not provided.')
        sys.exit(1)

    print('\nConfirmation accepted. Proceeding...\n')


# ======================================================================
# SHARED ERROR PARSING
# ======================================================================

def extract_error(response):
    """Return (error_code, summary_message) extracted from Atlassian Admin API."""
    status = response.status_code

    try:
        data = response.json() if response.text else {}
    except Exception:
        return (status, '(Invalid JSON response)')

    # ProxyError: {"code":403, "message":"..."}
    if isinstance(data, dict) and "message" in data and "code" in data:
        return (data.get("code"), data.get("message"))

    # ApplicationErrors: {"errors":[{...}]}
    if isinstance(data, dict) and "errors" in data:
        parts = []
        for err in data["errors"]:
            c = err.get("code", "N/A")
            t = err.get("title", "")
            d = err.get("detail", "")
            parts.append(f"{c}: {t}. {d}")
        return (status, " | ".join(parts))

    # Fallback
    return (status, str(data))


# ======================================================================
# ACTION HANDLERS
# ======================================================================

def remove_access(account_id, email):
    url = f'https://api.atlassian.com/admin/v1/orgs/{org_id}/directory/users/{account_id}'

    if dry_run:
        print(f"[DRY-RUN] Would REMOVE: {account_id} ({email})")
        print(f"[DRY-RUN] DELETE {url}")
        log_action(account_id, email, 'remove', None, 'DRY-RUN')
        return

    response = requests.delete(url, headers=headers)
    status = response.status_code

    if status == 204:
        print(f"REMOVE -> {account_id} ({email}) | Success")
        log_action(account_id, email, 'remove', None, 'Success')
        return

    error_code, summary = extract_error(response)
    print(f"REMOVE FAILED -> {account_id} ({email}) | {status} | {summary}")
    log_action(account_id, email, 'remove', error_code, summary)


def suspend_user(account_id, email):
    url = (
        f'https://api.atlassian.com/admin/v2/orgs/{org_id}/directories/'
        f'{directory_id}/users/{account_id}/suspend'
    )

    if dry_run:
        print(f"[DRY-RUN] Would SUSPEND: {account_id} ({email})")
        print(f"[DRY-RUN] POST {url}")
        log_action(account_id, email, 'suspend', None, 'DRY-RUN')
        return

    response = requests.post(url, headers=headers)
    status = response.status_code

    if status == 200:
        print(f"SUSPEND -> {account_id} ({email}) | Success")
        log_action(account_id, email, 'suspend', None, 'Success')
        return

    error_code, summary = extract_error(response)
    print(f"SUSPEND FAILED -> {account_id} ({email}) | {status} | {summary}")
    log_action(account_id, email, 'suspend', error_code, summary)


def restore_user(account_id, email):
    url = (
        f'https://api.atlassian.com/admin/v2/orgs/{org_id}/directories/'
        f'{directory_id}/users/{account_id}/restore'
    )

    if dry_run:
        print(f"[DRY-RUN] Would RESTORE: {account_id} ({email})")
        print(f"[DRY-RUN] POST {url}")
        log_action(account_id, email, 'restore', None, 'DRY-RUN')
        return

    response = requests.post(url, headers=headers)
    status = response.status_code

    if status == 200:
        print(f"RESTORE -> {account_id} ({email}) | Success")
        log_action(account_id, email, 'restore', None, 'Success')
        return

    error_code, summary = extract_error(response)
    print(f"RESTORE FAILED -> {account_id} ({email}) | {status} | {summary}")
    log_action(account_id, email, 'restore', error_code, summary)


# ======================================================================
# CSV LOADING
# ======================================================================

def load_rows():
    rows = []

    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)  # Skip header

        for r in reader:
            if len(r) <= max(COL_ACCOUNT_ID, COL_EMAIL, COL_ACTION):
                continue

            account_id = r[COL_ACCOUNT_ID].strip()
            email = r[COL_EMAIL].strip() if r[COL_EMAIL] else ''
            action = r[COL_ACTION].strip().lower()

            rows.append((account_id, email, action))

    return rows


# ======================================================================
# MAIN
# ======================================================================

def main():
    rows = load_rows()
    actions_present = {r[2] for r in rows}

    # Require confirmation if ANY remove exists
    if 'remove' in actions_present and not dry_run:
        confirm_remove()

    for account_id, email, action in rows:

        if action == 'remove':
            remove_access(account_id, email)
        elif action == 'suspend':
            suspend_user(account_id, email)
        elif action == 'restore':
            restore_user(account_id, email)
        else:
            print(f"INVALID ACTION '{action}' for {account_id} ({email})")
            log_action(account_id, email, action, 'INVALID_ACTION', 'Failed')


if __name__ == '__main__':
    main()
