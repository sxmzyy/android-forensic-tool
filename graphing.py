import re
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from collections import Counter
import os
import pandas as pd
from fpdf import FPDF  # Correct import for FPDF
from tkinter import messagebox

def get_timestamps_from_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return None, []
    
    timestamps = []
    all_lines = []
    for line in lines:
        # Try standard datetime format
        date_match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', line)
        if date_match:
            try:
                ts = datetime.strptime(date_match.group(), "%Y-%m-%d %H:%M:%S")
                timestamps.append(ts)
                all_lines.append(line)
                continue
            except Exception:
                pass
        # Try unix timestamp
        unix_match = re.search(r'date=(\d+)', line)
        if unix_match:
            try:
                ts = datetime.fromtimestamp(int(unix_match.group(1)) / 1000)
                timestamps.append(ts)
                all_lines.append(line)
            except Exception:
                pass
        # Try logcat timestamp format
        logcat_match = re.search(r'(\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
        if logcat_match:
            try:
                today = datetime.now()
                date_str = f"{today.year}-{logcat_match.group(1)}"
                ts = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                if ts > today:
                    ts = ts.replace(year=today.year - 1)
                timestamps.append(ts)
                all_lines.append(line)
            except Exception:
                pass
    return all_lines, timestamps

def apply_time_filter(timestamps, lines, time_range):
    filtered_timestamps = []
    filtered_lines = []
    now = datetime.now()
    for i, ts in enumerate(timestamps):
        include = False
        if time_range == "Past 1 Hour" and now - ts <= timedelta(hours=1):
            include = True
        elif time_range == "Past 24 Hours" and now - ts <= timedelta(hours=24):
            include = True
        elif time_range == "Past 7 Days" and now - ts <= timedelta(days=7):
            include = True
        elif time_range == "All Time":
            include = True
        if include:
            filtered_timestamps.append(ts)
            filtered_lines.append(lines[i])
    return filtered_timestamps, filtered_lines

def plot_graph(graph_ax, graph_canvas, log_type, time_range):
    graph_ax.clear()
    if log_type in ["Call Logs", "SMS Logs"]:
        path = "logs/call_logs.txt" if log_type == "Call Logs" else "logs/sms_logs.txt"
        lines, timestamps = get_timestamps_from_file(path)
        if lines is None or not lines:
            graph_ax.text(0.5, 0.5, f"{log_type} file not found or empty", fontsize=14, ha='center')
            graph_canvas.draw()
            return
        timestamps, lines = apply_time_filter(timestamps, lines, time_range)
        if not timestamps:
            graph_ax.text(0.5, 0.5, "No data in selected time range", fontsize=12, ha='center')
            graph_canvas.draw()
            return
        activity_per_hour = {}
        for ts in timestamps:
            hour = ts.replace(minute=0, second=0, microsecond=0)
            activity_per_hour[hour] = activity_per_hour.get(hour, 0) + 1
        sorted_times = sorted(activity_per_hour.keys())
        counts = [activity_per_hour[t] for t in sorted_times]
        graph_ax.plot(sorted_times, counts, marker="o", color="lime", linewidth=2)
        graph_ax.set_title(f"{log_type} Activity Over Time", color="lime", fontsize=12)
        graph_ax.set_ylabel("Count", color="lime")
        graph_ax.set_xlabel("Time", color="lime")
        graph_ax.tick_params(axis='x', colors="lime")
        graph_ax.tick_params(axis='y', colors="lime")
        graph_ax.grid(True, alpha=0.3)
        graph_ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        graph_canvas.draw()
    elif log_type == "Top SMS Senders":
        lines, timestamps = get_timestamps_from_file("logs/sms_logs.txt")
        if lines is None or not lines:
            graph_ax.text(0.5, 0.5, "SMS log file not found or empty", fontsize=14, ha='center')
            graph_canvas.draw()
            return
        timestamps, lines = apply_time_filter(timestamps, lines, time_range)
        if not timestamps:
            graph_ax.text(0.5, 0.5, "No data in selected time range", fontsize=12, ha='center')
            graph_canvas.draw()
            return
        senders = []
        for line in lines:
            # Check multiple possibilities: from:, address:, sender:
            match = re.search(r'(?:from:|address:|sender:)\s*(\+?\d+)', line, re.IGNORECASE)
            if match:
                senders.append(match.group(1))
        if not senders:
            graph_ax.text(0.5, 0.5, "No sender data found in logs", fontsize=12, ha='center')
            graph_canvas.draw()
            return
        counter = Counter(senders)
        top_senders = counter.most_common(10)
        labels = [s[0] for s in top_senders]
        counts = [s[1] for s in top_senders]
        bars = graph_ax.barh(labels[::-1], counts[::-1], color="lime")
        graph_ax.set_title("Top 10 SMS Senders", color="lime", fontsize=12)
        graph_ax.set_xlabel("Number of Messages", color="lime")
        graph_ax.tick_params(axis='x', colors="lime")
        graph_ax.tick_params(axis='y', colors="lime")
        graph_ax.grid(True, axis='x', alpha=0.3)
        for i, bar in enumerate(bars):
            width = bar.get_width()
            graph_ax.text(width + 0.3, bar.get_y() + bar.get_height()/2, str(int(width)),
                          ha='left', va='center', color='lime')
        graph_canvas.draw()
    elif log_type == "Logcat Activity":
        lines, timestamps = get_timestamps_from_file("logs/android_logcat.txt")
        if lines is None or not lines:
            graph_ax.text(0.5, 0.5, "Logcat file not found or empty", fontsize=14, ha='center')
            graph_canvas.draw()
            return
        timestamps, lines = apply_time_filter(timestamps, lines, time_range)
        if not timestamps:
            graph_ax.text(0.5, 0.5, "No logcat activity in selected time range", fontsize=12, ha='center')
            graph_canvas.draw()
            return
        activity_per_hour = {}
        for ts in timestamps:
            hour = ts.replace(minute=0, second=0, microsecond=0)
            activity_per_hour[hour] = activity_per_hour.get(hour, 0) + 1
        sorted_times = sorted(activity_per_hour.keys())
        counts = [activity_per_hour[t] for t in sorted_times]
        graph_ax.plot(sorted_times, counts, marker="o", linestyle="-", color="lime", linewidth=2)
        graph_ax.set_title("Logcat Activity Over Time", color="lime", fontsize=12)
        graph_ax.set_ylabel("Number of Entries", color="lime")
        graph_ax.set_xlabel("Time", color="lime")
        graph_ax.tick_params(axis='x', colors="lime")
        graph_ax.tick_params(axis='y', colors="lime")
        graph_ax.grid(True, alpha=0.3)
        graph_ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        graph_canvas.draw()

def plot_frequent_callers(graph_ax, graph_canvas, time_range):
    try:
        with open("logs/call_logs.txt", "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except FileNotFoundError:
        graph_ax.clear()
        graph_ax.text(0.5, 0.5, "Call log file not found", fontsize=14, ha='center')
        graph_canvas.draw()
        return
    now = datetime.now()
    filtered_lines = []
    for line in lines:
        date_match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', line)
        unix_match = re.search(r'date=(\d+)', line)
        include = False
        if date_match:
            try:
                ts = datetime.strptime(date_match.group(), "%Y-%m-%d %H:%M:%S")
                if (time_range == "Past 1 Hour" and now - ts <= timedelta(hours=1)) or \
                   (time_range == "Past 24 Hours" and now - ts <= timedelta(hours=24)) or \
                   (time_range == "Past 7 Days" and now - ts <= timedelta(days=7)) or \
                   (time_range == "All Time"):
                    include = True
            except:
                pass
        elif unix_match:
            try:
                ts = datetime.fromtimestamp(int(unix_match.group(1)) / 1000)
                if (time_range == "Past 1 Hour" and now - ts <= timedelta(hours=1)) or \
                   (time_range == "Past 24 Hours" and now - ts <= timedelta(hours=24)) or \
                   (time_range == "Past 7 Days" and now - ts <= timedelta(days=7)) or \
                   (time_range == "All Time"):
                    include = True
            except:
                pass
        if include or time_range == "All Time":
            filtered_lines.append(line)
    if not filtered_lines:
        graph_ax.clear()
        graph_ax.text(0.5, 0.5, "No call data in selected time range", fontsize=12, ha='center')
        graph_canvas.draw()
        return
    numbers = []
    # NEW extraction logic: use a broad regex to capture phone numbers (optionally starting with +, 10 to 15 digits)
    for line in filtered_lines:
        matches = re.findall(r'\+?\d{10,15}', line)
        if matches:
            # Choose the first match from each line as the representative phone number
            numbers.append(matches[0])
    if not numbers:
        graph_ax.clear()
        graph_ax.text(0.5, 0.5, "No phone numbers found in logs", fontsize=12, ha='center')
        graph_canvas.draw()
        return
    counter = Counter(numbers)
    top_callers = counter.most_common(10)
    labels = [x[0] for x in top_callers]
    counts = [x[1] for x in top_callers]
    graph_ax.clear()
    bars = graph_ax.barh(labels[::-1], counts[::-1], color="lime")
    graph_ax.set_title("Top 10 Frequent Callers", color="lime", fontsize=12)
    graph_ax.set_xlabel("Number of Calls", color="lime")
    graph_ax.tick_params(axis='x', colors="lime")
    graph_ax.tick_params(axis='y', colors="lime")
    graph_ax.grid(True, axis='x', alpha=0.3)
    for i, bar in enumerate(bars):
        width = bar.get_width()
        graph_ax.text(width + 0.3, bar.get_y() + bar.get_height()/2, str(int(width)),
                      ha='left', va='center', color='lime')
    graph_canvas.draw()

def export_chart(fig, filename):
    try:
        os.makedirs("logs/exports", exist_ok=True)
        filepath = os.path.join("logs/exports", filename)
        fig.savefig(filepath, dpi=300, bbox_inches='tight')
        messagebox.showinfo("Export Successful", f"Chart exported to {filepath}")
    except Exception as e:
        messagebox.showerror("Export Failed", f"Failed to export chart: {str(e)}")

def export_graph_data(graph_ax, time_combo, log_type):
    try:
        data = []
        if graph_ax.lines:
            x_data = graph_ax.lines[0].get_xdata()
            y_data = graph_ax.lines[0].get_ydata()
            data = list(zip(x_data, y_data))
        elif graph_ax.patches:
            bars = graph_ax.patches
            tick_labels = [tick.get_text() for tick in graph_ax.get_yticklabels()]
            values = [bar.get_width() for bar in bars]
            data = list(zip(tick_labels[::-1], values[::-1]))
        if not data:
            messagebox.showwarning("Export Warning", "No graph data to export.")
            return
        os.makedirs("logs/exports", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        df = pd.DataFrame(data, columns=["Label/Time", "Count"])
        filepath = f"logs/exports/graph_export_{timestamp}.csv"
        df.to_csv(filepath, index=False)
        messagebox.showinfo("Export Successful", f"Data exported to {filepath}")
    except Exception as e:
        messagebox.showerror("Export Failed", f"Failed to export data: {str(e)}")
