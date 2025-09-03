# log_monitor.py
import threading
import time
import re
import os
import queue
from config import monitoring_active, LOG_TYPES
from scripts.android_logs import monitor_logs

def start_monitoring(update_live_monitor, log_queue):
    """
    Called when the user presses "Start Live Monitoring". 
    Sets monitoring_active = True and spawns a background thread 
    that reads logs via monitor_logs.
    """
    global monitoring_active
    if not monitoring_active:
        monitoring_active = True
        start_monitoring._thread = threading.Thread(target=monitor_thread, args=(update_live_monitor, log_queue), daemon=True)
        start_monitoring._thread.start()
        update_live_monitor("🔍 Starting live monitoring...\n")
    else:
        update_live_monitor("⚠️ Monitoring is already running\n")

def stop_monitoring(update_live_monitor):
    """
    Called when the user presses "Stop Live Monitoring".
    Sets monitoring_active = False so the background thread 
    ends gracefully, showing "Monitoring stopped".
    """
    global monitoring_active
    if monitoring_active:
        monitoring_active = False
        update_live_monitor("⏹️ Stopping live monitoring...\n")
    else:
        update_live_monitor("⚠️ Monitoring is not running\n")

def monitor_thread(update_live_monitor, log_queue):
    """
    Actual background thread that calls monitor_logs with a callback.
    Reads until user presses Stop or the process ends.
    """
    try:
        def handle_log(log):
            # Put updates in the queue so they appear in the main UI
            log_queue.put(('update', log))
            # Optional categorization:
            # for log_type, info in LOG_TYPES.items():
            #     if re.search(info["pattern"], log, re.IGNORECASE):
            #         log_queue.put(('categorize', (log_type, log)))
        monitor_logs(handle_log)
    except Exception as e:
        log_queue.put(('error', f"Monitoring error: {str(e)}"))
    finally:
        try:
            # Terminate the process (if not already terminated)
            process = None
            # (The monitor_logs function internally terminates its process.)
        except Exception as term_e:
            log_queue.put(('error', f"Error terminating process: {term_e}"))
        # Use the global monitoring_active value directly (do not re-import)
        global monitoring_active
        if not monitoring_active:
            log_queue.put(('status', "Monitoring stopped"))
        else:
            log_queue.put(('error', "Logcat process ended unexpectedly."))
