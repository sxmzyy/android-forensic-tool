import os
import queue
import tkinter as tk
import tkinter.ttk as ttk
import matplotlib.pyplot as plt
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading  # Import the threading module

from config import LOG_TYPES, log_queue
from gui import (create_main_window, setup_style, create_tabs, create_widgets,
                 create_live_monitoring_buttons, create_graph_controls,
                 create_filter_controls, create_filter_output, create_export_frame, create_menu)
from log_monitor import start_monitoring, stop_monitoring
from graphing import plot_graph, plot_frequent_callers, export_chart, export_graph_data
from filtering import filter_logs, load_filtered_logs, save_filtered_logs
from reporting import export_full_report
from scripts.android_logs import get_logcat, get_call_logs, get_sms_logs

# Initialize log queue
log_queue = queue.Queue()

# Create main window and set style
root = create_main_window()
setup_style(root)

# Create main tabs and widgets
tabs, tab_control = create_tabs(root)
widgets = create_widgets(tabs)

# -------------------------------------------------------------------
# Dictionary to store references to Analysis Notebook text widgets
# -------------------------------------------------------------------
analysis_widgets = {}

# -------------------------------------------------------------------
# NEW FUNCTION: Categorize logcat logs into Logcat Types sub-tabs
# -------------------------------------------------------------------
import re
def categorize_logcat_logs():
    try:
        with open("logs/android_logcat.txt", "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    except FileNotFoundError:
        return

    # Clear previous content in each Logcat Types text widget
    for log_type in LOG_TYPES:
        text_widget = widgets["logcat_type_texts"][log_type]
        text_widget.config(state=tk.NORMAL)
        text_widget.delete(1.0, tk.END)
        text_widget.config(state=tk.DISABLED)

    # Process each line from the logcat file
    for line in lines:
        matched = False
        for log_type, info in LOG_TYPES.items():
            pattern = info["pattern"]
            if re.search(pattern, line, re.IGNORECASE):
                text_widget = widgets["logcat_type_texts"].get(log_type)
                if text_widget:
                    text_widget.config(state=tk.NORMAL)
                    text_widget.insert(tk.END, line + "\n")
                    text_widget.see(tk.END)
                    text_widget.config(state=tk.DISABLED)
                matched = True
                break  # Insert line only into the first matching category
        if not matched:
            # Optionally, handle lines that do not match any category
            pass

# -------------------------------------------------------------------
# Add Extract Logs Button in the "Extract Logs" tab
# -------------------------------------------------------------------
def extract_logs():
    widgets["output_text"].config(state=tk.NORMAL)
    widgets["output_text"].insert(tk.END, "Starting log extraction...\n")
    widgets["output_text"].see(tk.END)
    # Remove try/except so errors cause a crash (as requested)
    get_logcat()
    get_call_logs()
    get_sms_logs()
    # Reload logcat logs into "Logcat Logs" tab
    with open("logs/android_logcat.txt", "r", encoding="utf-8") as f:
        data = f.read()
    widgets["logcat_text"].delete(1.0, tk.END)
    widgets["logcat_text"].insert(tk.END, data)

    # Load all logs into "All Logs" text widget
    all_text = ""
    log_files = [("Logcat", "logs/android_logcat.txt"),
                 ("Call", "logs/call_logs.txt"),
                 ("SMS", "logs/sms_logs.txt")]
    for title, path in log_files:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as ff:
                all_text += f"\n===== {title} Logs =====\n" + ff.read() + "\n"
        else:
            all_text += f"\n⚠️ {title} log file not found.\n"
    widgets["all_logs_text"].delete(1.0, tk.END)
    widgets["all_logs_text"].insert(tk.END, all_text)

    # Categorize logcat lines into logcat types sub-tabs
    categorize_logcat_logs()

    # ---------------------------------------------
    # Populate the Analysis Notebook with real logs
    # ---------------------------------------------
    # 1) Call Logs
    if os.path.exists("logs/call_logs.txt"):
        with open("logs/call_logs.txt", "r", encoding="utf-8", errors="replace") as f_call:
            call_data = f_call.read()
    else:
        call_data = "No call logs found."
    analysis_widgets["call_log_text"].config(state=tk.NORMAL)
    analysis_widgets["call_log_text"].delete(1.0, tk.END)
    analysis_widgets["call_log_text"].insert(tk.END, call_data)
    analysis_widgets["call_log_text"].config(state=tk.DISABLED)

    # 2) SMS Logs
    if os.path.exists("logs/sms_logs.txt"):
        with open("logs/sms_logs.txt", "r", encoding="utf-8", errors="replace") as f_sms:
            sms_data = f_sms.read()
    else:
        sms_data = "No SMS logs found."
    analysis_widgets["sms_text"].config(state=tk.NORMAL)
    analysis_widgets["sms_text"].delete(1.0, tk.END)
    analysis_widgets["sms_text"].insert(tk.END, sms_data)
    analysis_widgets["sms_text"].config(state=tk.DISABLED)

    # 3) Logcat
    if os.path.exists("logs/android_logcat.txt"):
        with open("logs/android_logcat.txt", "r", encoding="utf-8", errors="replace") as f_lcat:
            logcat_data = f_lcat.read()
    else:
        logcat_data = "No raw logcat data available."
    analysis_widgets["logcat_text"].config(state=tk.NORMAL)
    analysis_widgets["logcat_text"].delete(1.0, tk.END)
    analysis_widgets["logcat_text"].insert(tk.END, logcat_data)
    analysis_widgets["logcat_text"].config(state=tk.DISABLED)

    # The "Filter" tab is left as placeholder. You could show "logs/filtered_logs.txt" here if desired.

    widgets["output_text"].insert(tk.END, "✅ Logs extracted successfully!\n")
    widgets["output_text"].see(tk.END)
    widgets["output_text"].config(state=tk.DISABLED)

# --- THREADED FUNCTION WRAPPER for extract_logs ---
def extract_logs_threaded():
    """Runs the extract_logs function in a separate thread to avoid freezing the GUI."""
    thread = threading.Thread(target=extract_logs, daemon=True)
    thread.start()

extract_button = tk.Button(tabs["Extract"], text="Extract Logs", bg="gray", fg="black", command=extract_logs_threaded)
extract_button.pack(pady=5)

# -------------------------------------------------------------------
# Create live monitoring buttons and assign commands
# -------------------------------------------------------------------
start_btn, stop_btn = create_live_monitoring_buttons(tabs["Live"])
# This part is already well-designed with a queue, so no changes are needed here.
start_btn.configure(command=lambda: start_monitoring(lambda log: log_queue.put(('update', log)), log_queue))
stop_btn.configure(command=lambda: stop_monitoring(lambda log: log_queue.put(('update', log))))

# -------------------------------------------------------------------
# Create graph controls and set up matplotlib figure and canvas
# -------------------------------------------------------------------
graph_controls = create_graph_controls(tabs["Graphs"])
graph_controls["logtype_combo"]["values"] = ["Call Logs", "SMS Logs", "Logcat Activity"]
graph_controls["logtype_combo"].set("Call Logs")
graph_fig, graph_ax = plt.subplots(figsize=(7, 4))
graph_canvas = FigureCanvasTkAgg(graph_fig, master=tabs["Graphs"])
graph_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=10)

# --- THREADED FUNCTION WRAPPERS for plotting ---
def plot_graph_threaded():
    """Runs plot_graph in a thread to prevent freezing."""
    # Get values from widgets in the main thread before passing to the new thread
    log_type = graph_controls["logtype_combo"].get()
    time_range = graph_controls["time_combo"].get()
    thread = threading.Thread(target=plot_graph, args=(graph_ax, graph_canvas, log_type, time_range), daemon=True)
    thread.start()

def plot_frequent_callers_threaded():
    """Runs plot_frequent_callers in a thread to prevent freezing."""
    time_range = graph_controls["time_combo"].get()
    thread = threading.Thread(target=plot_frequent_callers, args=(graph_ax, graph_canvas, time_range), daemon=True)
    thread.start()

graph_controls["graph_btn"].configure(command=plot_graph_threaded)
graph_controls["freq_btn"].configure(command=plot_frequent_callers_threaded)

# -------------------------------------------------------------------
# Create export frame and assign export commands
# -------------------------------------------------------------------
export_controls = create_export_frame(root)

# --- THREADED FUNCTION WRAPPERS for exporting ---
def export_full_report_threaded():
    """Runs export_full_report in a thread."""
    thread = threading.Thread(target=export_full_report, daemon=True)
    thread.start()

def export_chart_threaded(file_format):
    """Runs export_chart in a thread."""
    thread = threading.Thread(target=export_chart, args=(graph_fig, f"graph_export.{file_format}"), daemon=True)
    thread.start()

def export_graph_data_threaded():
    """Runs export_graph_data in a thread."""
    time_range = graph_controls["time_combo"].get()
    log_type = graph_controls["logtype_combo"].get()
    thread = threading.Thread(target=export_graph_data, args=(graph_ax, time_range, log_type), daemon=True)
    thread.start()

export_controls["full"].configure(command=export_full_report_threaded)
export_controls["png"].configure(command=lambda: export_chart_threaded("png"))
export_controls["pdf"].configure(command=lambda: export_chart_threaded("pdf"))
export_controls["csv"].configure(command=export_graph_data_threaded)

# -------------------------------------------------------------------
# Create filter controls and output widget; assign filter button commands
# -------------------------------------------------------------------
filter_controls = create_filter_controls(tabs["Filter"])
filter_output_widget = create_filter_output(tabs["Filter"])
def apply_filter():
    chosen_logtype = filter_controls["logtype"].get()
    chosen_time_range = filter_controls["time"].get()
    chosen_severity = filter_controls["severity"].get()
    chosen_subtype = filter_controls["subtype"].get()
    chosen_keyword = filter_controls["keyword"].get()

    if chosen_logtype == "Logcat":
        input_file = "logs/android_logcat.txt"
    elif chosen_logtype == "Calls":
        input_file = "logs/call_logs.txt"
    elif chosen_logtype == "SMS":
        input_file = "logs/sms_logs.txt"
    else:
        input_file = "logs/android_logcat.txt"

    filter_logs(
        input_file,
        keyword=chosen_keyword,
        time_range=chosen_time_range,
        severity=chosen_severity,
        subtype=chosen_subtype,
        output_file="logs/filtered_logs.txt"
    )
    load_filtered_logs(filter_output_widget)

# --- THREADED FUNCTION WRAPPER for filtering ---
def apply_filter_threaded():
    """Runs apply_filter in a thread."""
    thread = threading.Thread(target=apply_filter, daemon=True)
    thread.start()

filter_controls["apply"].configure(command=apply_filter_threaded)
filter_controls["save"].configure(command=save_filtered_logs) # Saving is usually fast, but can be threaded if needed

# -------------------------------------------------------------------
# Create main menu
# -------------------------------------------------------------------
menu = create_menu(root, tab_control)

# Fix "Import Logs" command to use the threaded function
for i in range(menu.index("end") + 1):
    try:
        entry_label = menu.entrycget(i, "label")
    except tk.TclError:
        continue
    if entry_label == "File":
        file_menu_name = menu.entrycget(i, "menu")
        file_menu = menu.nametowidget(file_menu_name)
        for j in range(file_menu.index("end") + 1):
            try:
                if file_menu.entrycget(j, "label") == "Import Logs":
                    file_menu.entryconfigure(j, command=extract_logs_threaded)
                    break
            except tk.TclError:
                continue
        break

# -------------------------------------------------------------------
# Define update_live_monitor to update the live_text widget
# -------------------------------------------------------------------
def update_live_monitor(log):
    widgets["live_text"].config(state=tk.NORMAL)
    widgets["live_text"].insert(tk.END, log)
    widgets["live_text"].see(tk.END)
    if int(widgets["live_text"].index('end-1c').split('.')[0]) > 1000:
        widgets["live_text"].delete(1.0, "100.0")
    widgets["live_text"].config(state=tk.DISABLED)

# -------------------------------------------------------------------
# Process log queue periodically
# -------------------------------------------------------------------
def process_log_queue():
    if not root.winfo_exists():
        return
    try:
        while not log_queue.empty():
            entry_type, data = log_queue.get_nowait()
            if entry_type == 'update':
                update_live_monitor(data + "\n")
            elif entry_type == 'categorize':
                log_type, log_line = data
                text_widget = widgets["logcat_type_texts"].get(log_type)
                if text_widget:
                    text_widget.config(state=tk.NORMAL)
                    text_widget.insert(tk.END, log_line + "\n")
                    text_widget.see(tk.END)
                    text_widget.config(state=tk.DISABLED)
            elif entry_type == 'error':
                messagebox.showerror("Monitoring Error", data)
            elif entry_type == 'status':
                update_live_monitor(f"⭐ {data}\n")
    except Exception as e:
        print("Error processing log queue:", e)
    if root.winfo_exists():
        root.after(100, process_log_queue)

process_log_queue()

# -------------------------------------------------------------------
# (Optional) Create a secondary notebook for analysis if desired.
# -------------------------------------------------------------------
from tkinter import scrolledtext

analysis_notebook = ttk.Notebook(root)

tab_call_log = tk.Frame(analysis_notebook)
tab_sms = tk.Frame(analysis_notebook)
tab_logcat_secondary = tk.Frame(analysis_notebook)
tab_filter_secondary = tk.Frame(analysis_notebook)

call_log_text = scrolledtext.ScrolledText(tab_call_log, wrap=tk.WORD, bg="black", fg="lime", font=("Consolas", 10))
call_log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
analysis_widgets["call_log_text"] = call_log_text

sms_text = scrolledtext.ScrolledText(tab_sms, wrap=tk.WORD, bg="black", fg="lime", font=("Consolas", 10))
sms_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
analysis_widgets["sms_text"] = sms_text

logcat_text = scrolledtext.ScrolledText(tab_logcat_secondary, wrap=tk.WORD, bg="black", fg="lime", font=("Consolas", 10))
logcat_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
analysis_widgets["logcat_text"] = logcat_text

filter_analysis_text = scrolledtext.ScrolledText(tab_filter_secondary, wrap=tk.WORD, bg="black", fg="lime", font=("Consolas", 10))
filter_analysis_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
analysis_widgets["filter_text"] = filter_analysis_text

analysis_notebook.add(tab_call_log, text="Call Logs")
analysis_notebook.add(tab_sms, text="SMS")
analysis_notebook.add(tab_logcat_secondary, text="Logcat")
analysis_notebook.add(tab_filter_secondary, text="Filter")

analysis_notebook.pack(expand=True, fill='both')

if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    os.makedirs("logs/logcat_types", exist_ok=True)
    os.makedirs("logs/exports", exist_ok=True)

    messagebox.showinfo("Welcome",
        "Welcome to the Android Forensic Analyzer!\n\n"
        "This tool helps you analyze Android logs for forensic investigation. "
        "Start by importing logs using the 'Import Logs' option in the File menu.")

    root.mainloop()