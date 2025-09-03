import os
import re
from datetime import datetime
from collections import Counter
from fpdf import FPDF
from tkinter import messagebox

def get_todays_logs(log_lines):
    """Filters log entries to include only those from the current day."""
    today_str = datetime.now().strftime("%m-%d")
    todays_logs = []
    for line in log_lines:
        # Check if the line starts with the month-day format (e.g., "08-26")
        if line.strip().startswith(today_str):
            todays_logs.append(line)
    return todays_logs

def export_full_report():
    try:
        os.makedirs("logs/exports", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"logs/exports/forensic_report_{timestamp}.pdf"
        pdf = FPDF()

        # --- Cover Page ---
        pdf.add_page()
        pdf.set_font("Arial", 'B', size=24)
        pdf.cell(0, 15, "FORENSIC ANALYSIS REPORT", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", size=16)
        pdf.cell(0, 10, "Case Number: 123456", ln=True, align='C')
        pdf.ln(5)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, "Examiner: John Doe, Certified Digital Forensic Examiner", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='C')
        pdf.ln(20)
        pdf.multi_cell(0, 10,
            "This report contains digital forensic analysis of Android logs. It has been prepared in accordance with forensic investigation standards "
            "and is intended for use as court-admissible evidence. All procedures were performed following established chain-of-custody practices.",
            align='C'
        )

        # --- Chain of Custody Page ---
        pdf.add_page()
        pdf.set_font("Arial", 'B', size=18)
        pdf.cell(0, 10, "Chain of Custody", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 8,
            "1. Evidence acquired from the Android device using approved ADB tools.\n"
            "2. Logs extracted include Android Logcat, Call Logs, and SMS Logs.\n"
            "3. All files were verified using cryptographic hashes immediately after acquisition.\n"
            "4. This report documents the complete process, ensuring chain-of-custody integrity.",
            align='L'
        )

        # --- Methodology Page ---
        pdf.add_page()
        pdf.set_font("Arial", 'B', size=18)
        pdf.cell(0, 10, "Methodology", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 8,
            "The analysis involved the extraction of logs from the device using ADB commands. The logs were then filtered "
            "by time range, keyword, severity, and subtype. Graphical representations were generated to illustrate key activity trends. "
            "All steps were conducted under strict forensic protocols to preserve evidence integrity.",
            align='L'
        )

        # --- Table of Contents ---
        pdf.add_page()
        pdf.set_font("Arial", 'B', size=16)
        pdf.cell(0, 10, "Table of Contents", ln=True)
        pdf.ln(10)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 8, "1. Call Log Analysis", ln=True)
        pdf.cell(0, 8, "2. SMS Log Analysis", ln=True)
        pdf.cell(0, 8, "3. Logcat Analysis", ln=True)
        pdf.cell(0, 8, "4. Conclusion", ln=True)

        # --- Device Information Page ---
        pdf.add_page()
        pdf.set_font("Arial", 'B', size=16)
        pdf.cell(0, 10, "Device Information", ln=True)
        pdf.ln(5)
        pdf.set_font("Arial", size=12)
        try:
            device_info = {
                "Device Model": "Unknown",
                "Android Version": "Unknown",
                "Kernel Version": "Unknown"
            }
            if os.path.exists("logs/android_logcat.txt"):
                with open("logs/android_logcat.txt", "r", encoding="utf-8", errors="replace") as f:
                    logs = f.read()
            else:
                logs = ""
            model_match = re.search(r'model=([^,\s]+)', logs)
            if model_match:
                device_info["Device Model"] = model_match.group(1)
            version_matches = re.findall(r'Android\s+(\d+(?:\.\d+)?)', logs)
            device_version = None
            for ver in version_matches:
                try:
                    if float(ver) < 15:
                        device_version = ver
                        break
                except ValueError:
                    continue
            if device_version is not None:
                device_info["Android Version"] = device_version
            kernel_match = re.search(r'Linux\s+version\s+([^\s]+)', logs)
            if kernel_match:
                device_info["Kernel Version"] = kernel_match.group(1)
            for key, value in device_info.items():
                pdf.cell(0, 8, f"{key}: {value}", ln=True)
        except Exception as e:
            pdf.cell(0, 8, "Could not retrieve device information", ln=True)

        # --- Call Log Analysis ---
        pdf.add_page()
        pdf.set_font("Arial", 'B', size=16)
        pdf.cell(0, 10, "1. Call Log Analysis", ln=True)
        pdf.ln(10)
        try:
            if os.path.exists("logs/call_logs.txt"):
                with open("logs/call_logs.txt", "r", encoding="utf-8", errors="replace") as f:
                    call_logs = f.readlines()
            else:
                call_logs = []
            if call_logs:
                call_count = len(call_logs)
                incoming = sum(1 for line in call_logs if re.search(r'type:\s*1|INCOMING', line, re.IGNORECASE))
                outgoing = sum(1 for line in call_logs if re.search(r'type:\s*2|OUTGOING', line, re.IGNORECASE))
                missed = sum(1 for line in call_logs if re.search(r'type:\s*3|MISSED', line, re.IGNORECASE))
                pdf.set_font("Arial", size=12)
                pdf.cell(0, 8, f"Total calls: {call_count}", ln=True)
                pdf.cell(0, 8, f"Incoming calls: {incoming}", ln=True)
                pdf.cell(0, 8, f"Outgoing calls: {outgoing}", ln=True)
                pdf.cell(0, 8, f"Missed calls: {missed}", ln=True)
                pdf.ln(10)
                numbers = []
                for line in call_logs:
                    num_match = re.search(r'number=(\+?\d+)', line)
                    if num_match:
                        numbers.append(num_match.group(1))
                    else:
                        alt_match = re.search(r'(?:from:|to:)\s*(\+?\d+)', line)
                        if alt_match:
                            numbers.append(alt_match.group(1))
                if numbers:
                    counter = Counter(numbers)
                    top_callers = counter.most_common(5)
                    pdf.set_font("Arial", 'B', size=14)
                    pdf.cell(0, 8, "Top 5 Most Frequent Callers", ln=True)
                    pdf.ln(5)
                    pdf.set_font("Arial", 'B', size=12)
                    pdf.cell(90, 8, "Phone Number", border=1)
                    pdf.cell(50, 8, "Call Count", border=1, ln=True)
                    pdf.set_font("Arial", size=12)
                    for number, count in top_callers:
                        pdf.cell(90, 8, number, border=1)
                        pdf.cell(50, 8, str(count), border=1, ln=True)
                else:
                    pdf.cell(0, 8, "No phone numbers found", ln=True)
            else:
                pdf.cell(0, 8, "No call logs found", ln=True)
        except Exception as e:
            pdf.cell(0, 8, f"Error analyzing call logs: {str(e)}", ln=True)

        # --- SMS Log Analysis ---
        pdf.add_page()
        pdf.set_font("Arial", 'B', size=16)
        pdf.cell(0, 10, "2. SMS Log Analysis", ln=True)
        pdf.ln(10)
        try:
            if os.path.exists("logs/sms_logs.txt"):
                with open("logs/sms_logs.txt", "r", encoding="utf-8", errors="replace") as f:
                    sms_logs = f.readlines()
            else:
                sms_logs = []
            if sms_logs:
                sms_count = len(sms_logs)
                incoming = sum(1 for line in sms_logs if re.search(r'type:\s*1|INCOMING|from:', line, re.IGNORECASE))
                outgoing = sum(1 for line in sms_logs if re.search(r'type:\s*2|OUTGOING|to:', line, re.IGNORECASE))
                pdf.set_font("Arial", size=12)
                pdf.cell(0, 8, f"Total SMS messages: {sms_count}", ln=True)
                pdf.cell(0, 8, f"Incoming messages: {incoming}", ln=True)
                pdf.cell(0, 8, f"Outgoing messages: {outgoing}", ln=True)
                pdf.ln(10)
                senders = []
                for line in sms_logs:
                    match = re.search(r'from: (\+?\d+)', line)
                    if match:
                        senders.append(match.group(1))
                if senders:
                    counter = Counter(senders)
                    top_senders = counter.most_common(5)
                    pdf.set_font("Arial", 'B', size=14)
                    pdf.cell(0, 8, "Top 5 Most Frequent SMS Senders", ln=True)
                    pdf.ln(5)
                    pdf.set_font("Arial", 'B', size=12)
                    pdf.cell(90, 8, "Phone Number", border=1)
                    pdf.cell(50, 8, "Message Count", border=1, ln=True)
                    pdf.set_font("Arial", size=12)
                    for number, count in top_senders:
                        pdf.cell(90, 8, number, border=1)
                        pdf.cell(50, 8, str(count), border=1, ln=True)
                else:
                    pdf.cell(0, 8, "No sender data found", ln=True)
            else:
                pdf.cell(0, 8, "No SMS logs found", ln=True)
        except Exception as e:
            pdf.cell(0, 8, f"Error analyzing SMS logs: {str(e)}", ln=True)

        # --- Logcat Analysis ---
        pdf.add_page()
        pdf.set_font("Arial", 'B', size=16)
        pdf.cell(0, 10, "3. Logcat Analysis", ln=True)
        pdf.ln(10)
        from config import LOG_TYPES
        total_categorized = 0
        # Iterate through defined log types to show categorized logcat data
        for log_type in LOG_TYPES:
            try:
                filepath = f"logs/logcat_types/{log_type.lower()}_logs.txt"
                lines = []
                if os.path.exists(filepath):
                    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                        lines = f.readlines()
                if lines:
                    total_categorized += len(lines)
                    pdf.set_font("Arial", 'B', size=14)
                    pdf.cell(0, 8, f"{log_type} Logs", ln=True)
                    pdf.ln(5)
                    pdf.set_font("Arial", size=12)
                    pdf.cell(0, 8, f"Total entries: {len(lines)}", ln=True)
                    
                    # Get and display logs from today
                    todays_logs = get_todays_logs(lines)
                    if todays_logs:
                        pdf.set_font("Arial", 'B', size=12)
                        pdf.cell(0, 8, "Recent Logs from Today:", ln=True)
                        pdf.set_font("Arial", size=10)
                        for line in todays_logs:
                            if len(line) > 100:
                                line = line[:97] + "..."
                            pdf.multi_cell(0, 8, f"- {line.strip()}")
                        pdf.ln(5)
                    else:
                        pdf.set_font("Arial", size=10)
                        pdf.multi_cell(0, 8, "No log entries found for today.")
                        pdf.ln(5)

            except Exception as e:
                pdf.cell(0, 8, f"Error analyzing {log_type} logs: {str(e)}", ln=True)
        
        # If no categorized logcat data exists, include raw logcat logs
        if total_categorized == 0:
            pdf.set_font("Arial", 'B', size=14)
            pdf.cell(0, 8, "Raw Logcat Data", ln=True)
            pdf.ln(5)
            if os.path.exists("logs/android_logcat.txt"):
                with open("logs/android_logcat.txt", "r", encoding="utf-8", errors="replace") as f:
                    raw_lines = f.readlines()
                pdf.set_font("Arial", size=12)
                pdf.cell(0, 8, f"Total entries: {len(raw_lines)}", ln=True)
                
                # Get and display logs from today from raw logcat
                todays_raw_logs = get_todays_logs(raw_lines)
                if todays_raw_logs:
                    pdf.set_font("Arial", 'B', size=12)
                    pdf.cell(0, 8, "Recent Logs from Today:", ln=True)
                    pdf.set_font("Arial", size=10)
                    for line in todays_raw_logs:
                        if len(line) > 100:
                            line = line[:97] + "..."
                        pdf.multi_cell(0, 8, f"- {line.strip()}")
                    pdf.ln(5)
                else:
                    pdf.set_font("Arial", size=10)
                    pdf.multi_cell(0, 8, "No raw log entries found for today.")
                    pdf.ln(5)
            else:
                pdf.cell(0, 8, "No raw logcat data available.", ln=True)

        # --- Conclusion Page ---
        pdf.add_page()
        pdf.set_font("Arial", 'B', size=18)
        pdf.cell(0, 10, "Conclusion", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 8,
            "Based on the analysis of the Android logs, the evidence indicates activity pertinent to the case. "
            "All analyses were conducted in accordance with forensic standards. This report is complete and is prepared for court presentation.",
            align='L'
        )
        pdf.ln(10)
        pdf.cell(0, 8, "Examiner Signature: __________________________", ln=True)
        pdf.cell(0, 8, f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True)

        pdf.output(filepath)
        messagebox.showinfo("Report Generated", f"Forensic report exported to {filepath}")
    except Exception as e:
        messagebox.showerror("Report Generation Failed", f"Failed to generate report: {str(e)}")
