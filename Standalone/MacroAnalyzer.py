import csv
import os
import time
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from requests.auth import HTTPBasicAuth
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import webbrowser

VERSION = "2.2"

# =========================
# Utility Functions
# =========================
def today_str():
    return datetime.now().strftime('%Y-%m-%d')

def format_date_safe(date_str):
    if not date_str:
        return ''
    patterns = [
        '%Y-%m-%dT%H:%M:%S.%f%z',
        '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%d'
    ]
    if isinstance(date_str, str) and len(date_str) >= 6 and date_str[-6] in ['+', '-'] and date_str[-3] == ':':
        norm = date_str[:-3] + date_str[-2:]
    else:
        norm = date_str
    for p in patterns:
        try:
            dt = datetime.strptime(norm, p)
            return dt.strftime('%Y-%m-%d')
        except:
            continue
    return date_str

def get_user_display(user_obj):
    if not isinstance(user_obj, dict):
        return str(user_obj)
    return user_obj.get('displayName') or user_obj.get('username') or user_obj.get('accountId') or 'Unknown'

def safe_request(session, method, url, retries=3, backoff=2, **kwargs):
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            resp = session.request(method, url, **kwargs)
            if 200 <= resp.status_code < 300:
                return resp
            if 500 <= resp.status_code < 600:
                last_err = requests.HTTPError(f'{resp.status_code}: {resp.text}')
                if attempt < retries:
                    time.sleep(backoff * attempt)
                    continue
            resp.raise_for_status()
            return resp
        except requests.exceptions.RequestException as e:
            last_err = e
            if attempt < retries:
                time.sleep(backoff * attempt)
            else:
                raise
    if last_err:
        raise last_err

def build_baseurl_for_cloud(raw_baseurl):
    base = raw_baseurl.rstrip('/')
    if base.endswith('/wiki'):
        return base
    return base + '/wiki'

# =========================
# About and How To Windows
# =========================
def show_about(parent):
    win = tk.Toplevel(parent)
    win.title("About")
    win.transient(parent)
    win.resizable(False, False)
    win.grab_set()

    msg = (
        f"Confluence Macro Extractor (Server/DC & Cloud)\n"
        f"Version: {VERSION}\n\n"
        "Created by: Hugo Navia\n"
    )
    tk.Label(win, text=msg, justify='center', anchor='center', padx=16, pady=10).pack(fill='both', expand=True)

    email_lbl = tk.Label(win, text="hugo.navia@servicerocket.com", fg="blue", cursor="hand2")
    email_lbl.pack(pady=5)
    email_lbl.bind("<Button-1>", lambda e: webbrowser.open("mailto:hugo.navia@servicerocket.com"))

    desc = (
        "\nThis tool reads a macro list (CSV), queries Confluence for each macro usage,\n "
        "and exports a detailed CSV report plus a log summary."
    )
    tk.Label(win, text=desc, justify='center', anchor='center', padx=16, pady=8).pack(fill='both', expand=True)

    ttk.Button(win, text="Close", command=win.destroy).pack(pady=10)

def show_how_to(parent):
    win = tk.Toplevel(parent)
    win.title("How To")
    win.transient(parent)
    win.resizable(False, False)
    win.grab_set()
    st = scrolledtext.ScrolledText(win, wrap='word', width=80, height=22)
    st.pack(fill='both', expand=True, padx=8, pady=8)
    instructions = (
        "Step-by-Step Instructions:\n\n"
        "1) Prepare the Input CSV manually (the tool DOES NOT auto-export):\n"
        "   - Column 0 = Plugin Name\n"
        "   - Column 1 = Macro Name\n"
        "   Any other columns will be ignored. Rows with fewer than 2 columns are skipped.\n\n"
        "2) Launch the tool and pick the correct tab:\n"
        "   - Server / DC: provide Base URL and either PAT or Username/Password. You can choose to bypass SSL verification (Server/DC only).\n"
        "   - Cloud: provide Base URL (e.g. https://your-domain.atlassian.net), Email and API Token. Cloud always verifies SSL.\n\n"
        "3) Click 'Browse' and select your input CSV file.\n"
        "4) Click 'Start'. The progress bar shows macro processing progress.\n"
        "5) Output files (in the same folder as the input CSV):\n"
        "   - <input_basename>_result_<YYYY-MM-DD>.csv  (detailed results)\n"
        "   - <input_basename>_result_<YYYY-MM-DD>.log  (per-macro counts)\n\n"
        "Notes:\n"
        " - The script uses column positions (0 and 1) — header names are ignored.\n"
        " - Plugin Name column may be empty; the CSV will contain empty plugin cells in that case.\n"
    )
    st.insert('end', instructions)
    st.config(state='disabled')
    ttk.Button(win, text="Close", command=win.destroy).pack(pady=6)

# =========================
# Confluence Fetchers
# =========================
def fetch_all_results_for_macro(session, baseurl, macro, verify_ssl):
    all_results = []
    start = 0
    limit = 500
    while True:
        resp = safe_request(
            session, 'GET',
            f'{baseurl}/rest/api/content/search',
            params={'cql': f'macro="{macro}"', 'start': start, 'limit': limit},
            verify=verify_ssl
        )
        data = resp.json()
        results = data.get('results', []) or []
        all_results.extend(results)
        links = data.get('_links') or {}
        if 'next' in links:
            start += limit
        else:
            break
    return all_results

def fetch_page_details(session, baseurl, page_id, verify_ssl):
    resp = safe_request(
        session, 'GET',
        f'{baseurl}/rest/api/content/{page_id}',
        params={'expand': 'history,version,space'},
        verify=verify_ssl
    )
    page = resp.json()
    space_key = (page.get('space') or {}).get('key', '')
    title = page.get('title', '')
    history = page.get('history') or {}
    version = page.get('version') or {}
    creator = get_user_display(history.get('createdBy', {}))
    created_date = format_date_safe(history.get('createdDate'))
    last_modified_by = get_user_display(version.get('by', {}))
    last_modified_date = format_date_safe(version.get('when'))
    links = page.get('_links') or {}
    webui = links.get('webui', '')
    page_url = f'{baseurl}{webui}' if webui else ''
    return {
        'space_key': space_key,
        'title': title,
        'creator': creator,
        'created_date': created_date,
        'last_modified_by': last_modified_by,
        'last_modified_date': last_modified_date,
        'page_id': str(page.get('id', '')),
        'page_url': page_url
    }

# =========================
# Worker Function
# =========================
def run_confluence_job(config, csv_input_path, verify_ssl, progress_bar, on_done_callback):
    summary_counts = {}
    try:
        s = requests.Session()
        s.headers.update({'Accept': 'application/json'})

        if config['mode'] == 'DC':
            baseurl = config['baseurl'].rstrip('/')
            if config.get('auth') == 'PAT' and config.get('pat'):
                s.headers.update({'Authorization': f'Bearer {config["pat"]}'})
            else:
                s.auth = (config.get('username', ''), config.get('password', ''))
            verify_flag = verify_ssl
        else:
            baseurl = build_baseurl_for_cloud(config['baseurl'])
            s.auth = HTTPBasicAuth(config.get('email', ''), config.get('token', ''))
            verify_flag = True

        safe_request(s, 'GET', f'{baseurl}/rest/api/content', verify=verify_flag)

        tasks = []
        with open(csv_input_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if not row or len(row) < 2:
                    continue
                plugin = (row[0] or '').strip()
                macro = (row[1] or '').strip()
                if macro:
                    tasks.append((plugin, macro))

        if not tasks:
            raise ValueError('No macros found in CSV (expect at least two columns: [0]=Plugin, [1]=Macro).')

        out_dir = os.path.dirname(os.path.abspath(csv_input_path))
        base_name = os.path.splitext(os.path.basename(csv_input_path))[0]
        date_str = today_str()
        output_csv_path = os.path.join(out_dir, f'{base_name}_result_{date_str}.csv')
        log_path = os.path.join(out_dir, f'{base_name}_result_{date_str}.log')

        with open(output_csv_path, 'w', newline='', encoding='utf-8') as out_csv:
            writer = csv.writer(out_csv)
            writer.writerow([
                'Plugin Name','Macro Name','Space Key','Page Title','Creator',
                'Created Date','Last Modified by','Last Modified Date','Page ID','Page URL'
            ])

            progress_bar['value'] = 0
            progress_bar['maximum'] = len(tasks)

            with ThreadPoolExecutor(max_workers=6) as pool:
                future_map = {
                    pool.submit(fetch_all_results_for_macro, s, baseurl, macro, verify_flag): (plugin, macro)
                    for plugin, macro in tasks
                }
                for future in as_completed(future_map):
                    plugin, macro = future_map[future]
                    try:
                        results = future.result()
                    except:
                        results = []
                    summary_counts[macro] = summary_counts.get(macro, 0) + len(results)

                    page_futures = [
                        pool.submit(fetch_page_details, s, baseurl, str(p.get('id')), verify_flag)
                        for p in results
                    ]
                    for pf in as_completed(page_futures):
                        try:
                            details = pf.result()
                            writer.writerow([
                                plugin, macro,
                                details['space_key'], details['title'], details['creator'],
                                details['created_date'], details['last_modified_by'],
                                details['last_modified_date'], details['page_id'], details['page_url']
                            ])
                        except:
                            pass

                    try:
                        progress_bar['value'] += 1
                    except:
                        pass

        summary_text = '\n'.join([f'{m}: {c}' for m, c in sorted(summary_counts.items())]) if summary_counts else 'No results.'
        with open(log_path, 'w', encoding='utf-8') as lf:
            lf.write(summary_text + '\n')

        on_done_callback(summary_text, output_csv_path, log_path)

    except Exception as e:
        messagebox.showerror('Error', f'An error occurred: {e}')

# =========================
# Tkinter GUI
# =========================
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Confluence Macro Extractor (Server/DC & Cloud)')
        self.resizable(False, False)

        self.input_csv_path = tk.StringVar(value='')
        self.verify_ssl = tk.BooleanVar(value=True)

        menu_bar = tk.Menu(self)
        self.config(menu=menu_bar)
        menu_bar.add_command(label="How To", command=lambda: show_how_to(self))
        menu_bar.add_command(label="About", command=lambda: show_about(self))

        self.notebook = ttk.Notebook(self)
        self.tab_dc = ttk.Frame(self.notebook)
        self.tab_cloud = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_dc, text='Server / DC')
        self.notebook.add(self.tab_cloud, text='Cloud')
        self.notebook.pack(fill='x', expand=False, padx=6, pady=6)

        self._build_dc_tab(self.tab_dc)
        self._build_cloud_tab(self.tab_cloud)
        self._build_shared_io()

        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill='x', padx=8, pady=6)

        self.progress = ttk.Progressbar(bottom_frame, orient='horizontal', mode='determinate', length=560)
        self.progress.pack(fill='x', pady=(0, 2))
        self.progress_label = tk.Label(bottom_frame, text="Idle")
        self.progress_label.pack(fill='x', pady=(0, 2))

        self.btn_start = ttk.Button(bottom_frame, text='Start', command=self.on_start)
        self.btn_start.pack(pady=(2, 0))

    def _build_dc_tab(self, parent):
        ttk.Label(parent, text='Base URL:').grid(row=0, column=0, sticky='e', padx=6, pady=4)
        self.dc_baseurl = ttk.Entry(parent, width=50)
        self.dc_baseurl.grid(row=0, column=1, sticky='ew', padx=6, pady=4)
        parent.columnconfigure(1, weight=1)

        ttk.Label(parent, text='Auth Mode:').grid(row=1, column=0, sticky='e', padx=6, pady=4)
        self.dc_auth_mode = tk.StringVar(value='PAT')
        frame = ttk.Frame(parent); frame.grid(row=1, column=1, sticky='w')
        ttk.Radiobutton(frame, text='PAT', value='PAT', variable=self.dc_auth_mode, command=self._toggle_dc_auth).pack(side='left', padx=(0,6))
        ttk.Radiobutton(frame, text='Username + Password', value='BASIC', variable=self.dc_auth_mode, command=self._toggle_dc_auth).pack(side='left')

        ttk.Label(parent, text='Personal Access Token:').grid(row=2, column=0, sticky='e', padx=6, pady=4)
        self.dc_pat = ttk.Entry(parent, width=50, show='*')
        self.dc_pat.grid(row=2, column=1, sticky='ew', padx=6, pady=4)

        ttk.Label(parent, text='Username:').grid(row=3, column=0, sticky='e', padx=6, pady=4)
        self.dc_user = ttk.Entry(parent, width=50)
        self.dc_user.grid(row=3, column=1, sticky='ew', padx=6, pady=4)

        ttk.Label(parent, text='Password:').grid(row=4, column=0, sticky='e', padx=6, pady=4)
        self.dc_password = ttk.Entry(parent, width=50, show='*')
        self.dc_password.grid(row=4, column=1, sticky='ew', padx=6, pady=4)

        ttk.Label(parent, text='Verify SSL Certificates:').grid(row=5, column=0, sticky='e', padx=6, pady=4)
        ssl_frame = ttk.Frame(parent); ssl_frame.grid(row=5, column=1, sticky='w', padx=6, pady=4)
        ttk.Radiobutton(ssl_frame, text='Yes', value=True, variable=self.verify_ssl).pack(side='left', padx=(0,6))
        ttk.Radiobutton(ssl_frame, text='No', value=False, variable=self.verify_ssl).pack(side='left')

        self._toggle_dc_auth()

    def _toggle_dc_auth(self):
        if self.dc_auth_mode.get() == 'PAT':
            self.dc_pat.config(state='normal')
            self.dc_user.config(state='disabled'); self.dc_password.config(state='disabled')
            self.dc_user.delete(0, 'end'); self.dc_password.delete(0, 'end')
        else:
            self.dc_pat.config(state='disabled')
            self.dc_user.config(state='normal'); self.dc_password.config(state='normal')
            self.dc_pat.delete(0, 'end')

    def _build_cloud_tab(self, parent):
        ttk.Label(parent, text='Base URL:').grid(row=0, column=0, sticky='e', padx=6, pady=4)
        self.cloud_baseurl = ttk.Entry(parent, width=50)
        self.cloud_baseurl.grid(row=0, column=1, sticky='ew', padx=6, pady=4)

        ttk.Label(parent, text='Email:').grid(row=1, column=0, sticky='e', padx=6, pady=4)
        self.cloud_email = ttk.Entry(parent, width=50)
        self.cloud_email.grid(row=1, column=1, sticky='ew', padx=6, pady=4)

        ttk.Label(parent, text='API Token:').grid(row=2, column=0, sticky='e', padx=6, pady=4)
        self.cloud_token = ttk.Entry(parent, width=50, show='*')
        self.cloud_token.grid(row=2, column=1, sticky='ew', padx=6, pady=4)

        parent.columnconfigure(1, weight=1)

    def _build_shared_io(self):
        frame = ttk.Frame(self)
        frame.pack(fill='x', padx=8, pady=6)
        ttk.Label(frame, text='Input CSV:').grid(row=0, column=0, sticky='e', padx=(0,6))
        ttk.Entry(frame, textvariable=self.input_csv_path, width=50).grid(row=0, column=1, sticky='ew')
        ttk.Button(frame, text='Browse', command=self._browse_csv).grid(row=0, column=2, padx=(6,0))
        frame.columnconfigure(1, weight=1)

    def _browse_csv(self):
        path = filedialog.askopenfilename(filetypes=[('CSV Files', '*.csv')])
        if path:
            self.input_csv_path.set(path)

    def on_start(self):
        csv_input = self.input_csv_path.get()
        if not csv_input or not os.path.isfile(csv_input):
            messagebox.showerror('Input Error', 'Please select a valid input CSV.')
            return

        tab_index = self.notebook.index(self.notebook.select())
        if tab_index == 0:
            config = {'mode': 'DC', 'baseurl': self.dc_baseurl.get().strip(), 'auth': self.dc_auth_mode.get()}
            if config['auth'] == 'PAT':
                config['pat'] = self.dc_pat.get().strip()
            else:
                config['username'] = self.dc_user.get().strip()
                config['password'] = self.dc_password.get().strip()
        else:
            config = {
                'mode': 'Cloud',
                'baseurl': self.cloud_baseurl.get().strip(),
                'email': self.cloud_email.get().strip(),
                'token': self.cloud_token.get().strip()
            }

        self.btn_start.config(state='disabled')
        self.progress_label.config(text='Running...')
        threading.Thread(
            target=run_confluence_job,
            args=(config, csv_input, self.verify_ssl.get(), self.progress, self.on_done),
            daemon=True
        ).start()

    def on_done(self, summary_text, csv_path, log_path):
        try:
            self.btn_start.config(state='normal')
            self.progress_label.config(text='Completed')
        except:
            pass

        msg_win = tk.Toplevel(self)
        msg_win.title('Summary')
        msg_win.transient(self)
        msg_win.resizable(False, False)
        st = scrolledtext.ScrolledText(msg_win, wrap='word', width=80, height=20)
        st.pack(fill='both', expand=True, padx=8, pady=8)
        st.insert('end', f'Summary of results:\n\n{summary_text}\n\nCSV saved at: {csv_path}\nLog saved at: {log_path}')
        st.config(state='disabled')
        ttk.Button(msg_win, text='Close', command=msg_win.destroy).pack(pady=6)

if __name__ == '__main__':
    app = App()
    app.mainloop()
