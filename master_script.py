import csv
import importlib
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import firebase_admin
from firebase_admin import credentials, firestore
from tkcalendar import DateEntry
import pandas as pd
from google.cloud.firestore_v1 import FieldFilter

# Initialize Firebase Admin
cred = credentials.Certificate("firebase-credentials.json")
firebase_admin.initialize_app(cred, {
    'projectId': 'online-database-checking-tool',
})
db = firestore.client()

class DatabaseCheckerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Online Database Checking Tool")
        self.root.geometry("600x350")
        self.root.resizable(False, False)

        header = tk.Label(root, text="Online Database Checking Tool", font=("Arial", 18, "bold"))
        header.pack(pady=15)

        self.run_button = tk.Button(root, text="Run the check", font=("Arial", 12), command=self.start_check)
        self.run_button.pack(pady=10)

        self.progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=10)

        self.status_label = tk.Label(root, text="Status: Waiting to start", font=("Arial", 10))
        self.status_label.pack(pady=5)

        self.export_button = tk.Button(root, text="Export Results", font=("Arial", 12), command=self.export_results, state=tk.DISABLED)
        self.export_button.pack(pady=10)

        self.show_button = tk.Button(root, text="Show", font=("Arial", 12), command=self.open_log_window)
        self.show_button.pack(pady=10)  

        self.monthly_log_button = tk.Button(root, text="Monthly Log", font=("Arial", 12), command=self.open_monthly_log_window)
        self.monthly_log_button.pack(pady=10)

        self.results_file = None
        self.jobs = []
        self.results = []
        self.check_thread = None

    def start_check(self):
        self.run_button.config(state=tk.DISABLED)
        self.export_button.config(state=tk.DISABLED)
        self.status_label.config(text="Status: Running checks...")
        self.progress['value'] = 0
        self.results = []
        self.check_thread = threading.Thread(target=self.run_all_checks_gui)
        self.check_thread.start()

    def run_all_checks_gui(self):
        results_dir = "check_results"
        os.makedirs(results_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_file = os.path.join(results_dir, f"access_check_results_{timestamp}.csv")
        jobs = []
        with open("Onlie database Details.csv", "r") as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            for row in reader:
                if len(row) >= 4:
                    db_name = row[1]
                    url = row[2]
                    script_file = row[3]
                    if script_file and os.path.exists(os.path.join("Codes", script_file)):
                        jobs.append((db_name, url, script_file))
                    else:
                        result = {
                            'database_name': db_name,
                            'url': url,
                            'script_file': script_file,
                            'status': 'Script file not found',
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        self.results.append([db_name, url, script_file, "Script file not found", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                        # Store in Firestore
                        db.collection('database_checks').add(result)
        self.jobs = jobs
        total = len(jobs)
        with open(self.results_file, "w", newline="") as results:
            writer = csv.writer(results)
            writer.writerow(["Database Name", "URL", "Script File", "Status", "Timestamp"])
        if total == 0:
            self.status_label.config(text="Status: No jobs to run.")
            self.run_button.config(state=tk.NORMAL)
            return
        def run_check_gui(db_name, url, script_file):
            try:
                module_name = script_file.replace(".py", "")
                module = importlib.import_module(f"Codes.{module_name}")
                status = module.check_access(url)
                status_text = "Running" if status == 1 else "Not Running"
                result = {
                    'database_name': db_name,
                    'url': url,
                    'script_file': script_file,
                    'status': status_text,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                # Store in Firestore
                db.collection('database_checks').add(result)
                # Update monthly log
                update_monthly_log(db_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                return (db_name, url, script_file, status_text, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            except Exception as e:
                error_result = {
                    'database_name': db_name,
                    'url': url,
                    'script_file': script_file,
                    'status': f"Error: {str(e)}",
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                # Store error in Firestore
                db.collection('database_checks').add(error_result)
                return (db_name, url, script_file, f"Error: {str(e)}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        completed = 0
        with ThreadPoolExecutor(max_workers=6) as executor:
            future_to_job = {executor.submit(run_check_gui, db, url, script): (db, url, script) for db, url, script in jobs}
            for future in as_completed(future_to_job):
                result = future.result()
                self.results.append(result)
                completed += 1
                self.progress['value'] = (completed / total) * 100
                self.status_label.config(text=f"Status: Checked {completed}/{total} databases")
                self.root.update_idletasks()
                with open(self.results_file, "a", newline="") as results:
                    writer = csv.writer(results)
                    writer.writerow(result)
        self.status_label.config(text="Status: All checks complete!")
        self.export_button.config(state=tk.NORMAL)
        self.run_button.config(state=tk.NORMAL)

    def export_results(self):
        if not self.results_file or not os.path.exists(self.results_file):
            messagebox.showerror("Error", "No results file to export.")
            return
        save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if save_path:
            with open(self.results_file, "r", encoding="utf-8") as src, open(save_path, "w", encoding="utf-8") as dst:
                dst.write(src.read())
            messagebox.showinfo("Exported", f"Results exported to {save_path}")

    def open_log_window(self):
        log_win = tk.Toplevel(self.root)
        log_win.title("Historical Access Log")
        log_win.geometry("900x500")

        tk.Label(log_win, text="Start Date:").pack()
        start_date = DateEntry(log_win, width=12, background='darkblue', foreground='white', borderwidth=2)
        start_date.pack()
        tk.Label(log_win, text="End Date:").pack()
        end_date = DateEntry(log_win, width=12, background='darkblue', foreground='white', borderwidth=2)
        end_date.pack()

        fetch_btn = tk.Button(log_win, text="Fetch", command=lambda: self.fetch_and_display(log_win, start_date.get_date(), end_date.get_date()))
        fetch_btn.pack(pady=5)

        self.tree = ttk.Treeview(log_win, columns=("db", "url", "script", "status", "timestamp"), show="headings")
        for col in ("db", "url", "script", "status", "timestamp"):
            self.tree.heading(col, text=col.capitalize())
        self.tree.pack(expand=True, fill="both")

        export_btn = tk.Button(log_win, text="Export as CSV", command=self.export_log_data)
        export_btn.pack(pady=5)

        self.log_data = []

    def fetch_and_display(self, win, start, end):
        # Query Firestore for records between start and end
        start_date = start.strftime("%Y-%m-%d")
        end_date = end.strftime("%Y-%m-%d")
        docs = db.collection('database_checks') \
            .where(filter=FieldFilter('date', '>=', start_date)) \
            .where(filter=FieldFilter('date', '<=', end_date)) \
            .stream()
        self.log_data = []
        for doc in docs:
            data = doc.to_dict()
            self.tree.insert("", "end", values=(data['database_name'], data['url'], data['script_file'], data['status'], data['timestamp']))
            self.log_data.append(data)

    def export_log_data(self):
        if not self.log_data:
            messagebox.showerror("Error", "No data to export.")
            return
        save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if save_path:
            df = pd.DataFrame(self.log_data)
            df.to_csv(save_path, index=False)
            messagebox.showinfo("Exported", f"Log exported to {save_path}")

    def open_monthly_log_window(self):
        log_win = tk.Toplevel(self.root)
        log_win.title("Monthly Access Log")
        log_win.geometry("1200x600")

        # Month/year selectors
        tk.Label(log_win, text="Month:").pack()
        month_var = tk.IntVar(value=datetime.now().month)
        month_entry = tk.Spinbox(log_win, from_=1, to=12, textvariable=month_var, width=5)
        month_entry.pack()
        tk.Label(log_win, text="Year:").pack()
        year_var = tk.IntVar(value=datetime.now().year)
        year_entry = tk.Spinbox(log_win, from_=2000, to=2100, textvariable=year_var, width=7)
        year_entry.pack()

        fetch_btn = tk.Button(log_win, text="Fetch", command=lambda: self.fetch_monthly_grid(log_win, month_var.get(), year_var.get()))
        fetch_btn.pack(pady=5)

    def fetch_monthly_grid(self, win, month, year):
        # Get all DB names (from CSV or Firestore)
        db_names = self.get_all_db_names()  # Implement this to read from your CSV or Firestore

        # Prepare columns: 1..31
        days = [str(d) for d in range(1, 32)]
        columns = ["DB Name"] + days

        # Create Treeview
        tree = ttk.Treeview(win, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=80)
        tree.pack(expand=True, fill="both")

        # Fetch all records for the month from Firestore
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-31"
        docs = list(db.collection('database_checks') \
            .where(filter=FieldFilter('date', '>=', start_date)) \
            .where(filter=FieldFilter('date', '<=', end_date)) \
            .stream())

        access_dict = {db: {} for db in db_names}
        if docs:
            # Build a dict: {db_name: {day: time}}
            for doc in docs:
                data = doc.to_dict()
                dbn = data['database_name']
                # Defensive: check 'date' and 'time' fields
                if 'date' in data and 'time' in data:
                    try:
                        day = int(data['date'].split('-')[2])
                        access_dict[dbn][day] = data['time']
                    except Exception:
                        continue
        else:
            # Try to load from monthly_logs CSV
            import pandas as pd
            import os
            year_month = f"{year}{month:02d}"
            log_file = os.path.join("monthly_logs", f"monthly_log_{year_month}.csv")
            if os.path.exists(log_file):
                df = pd.read_csv(log_file, dtype=str)
                for _, row in df.iterrows():
                    dbn = row["Database Name"]
                    for day in days:
                        if day in row and pd.notna(row[day]) and row[day]:
                            try:
                                access_dict[dbn][int(day)] = row[day]
                            except Exception:
                                continue
        # Fill the grid
        for dbn in db_names:
            row = [dbn] + [access_dict[dbn].get(day, "") for day in range(1, 32)]
            tree.insert("", "end", values=row)

    def get_all_db_names(self):
        db_names = []
        with open("Onlie database Details.csv", "r", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip header
            for row in reader:
                if len(row) >= 2 and row[1].strip():
                    db_names.append(row[1].strip())
        return db_names

def update_monthly_log(db_name, timestamp, log_dir="monthly_logs"):
    now = datetime.now()
    year_month = now.strftime("%Y%m")
    day = str(now.day)
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"monthly_log_{year_month}.csv")

    # Try to read existing log
    if os.path.exists(log_file):
        df = pd.read_csv(log_file, dtype=str)
    else:
        # Create columns: Database Name, 1, 2, ..., 31
        columns = ["Database Name"] + [str(i) for i in range(1, 32)]
        df = pd.DataFrame(columns=columns)

    # Ensure db_name row exists
    if db_name not in df["Database Name"].values:
        new_row = {col: "" for col in df.columns}
        new_row["Database Name"] = db_name
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # Update the timestamp for the current day
    df.loc[df["Database Name"] == db_name, day] = timestamp

    # Save back to CSV
    df.to_csv(log_file, index=False)

def main():
    root = tk.Tk()
    app = DatabaseCheckerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()