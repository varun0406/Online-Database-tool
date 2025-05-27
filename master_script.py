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
                        self.results.append([
                            db_name, url, script_file, "Script file not found", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ])
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
                return (db_name, url, script_file, "Running" if status == 1 else "Not Running", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            except Exception as e:
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

def main():
    root = tk.Tk()
    app = DatabaseCheckerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 