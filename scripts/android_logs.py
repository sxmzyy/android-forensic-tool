import subprocess
import time
from datetime import datetime, timedelta
import os

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

def get_logcat():
    """
    Extract Android logcat logs from the past 24 hours.
    """
    since = (datetime.now() - timedelta(hours=24)).strftime("%m-%d %H:%M:%S.000")
    with open("logs/android_logcat.txt", "w", encoding="utf-8") as f:
        subprocess.run(["adb", "logcat", "-d", "-v", "time", "-T", since],
                       stdout=f, check=True)

def get_call_logs():
    """
    Extract Android call logs using the adb content query command.
    """
    try:
        result = subprocess.run(
            ["adb", "shell", "content", "query", "--uri", "content://call_log/calls"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True
        )
        output = result.stdout if result.stdout else "⚠️ No call logs found."
    except Exception as e:
        output = f"⚠️ Failed to extract call logs: {str(e)}"
    with open("logs/call_logs.txt", "w", encoding="utf-8") as f:
        f.write(output)

def get_sms_logs():
    """
    Extract Android SMS logs using the adb content query command.
    """
    try:
        result = subprocess.run(
            ["adb", "shell", "content", "query", "--uri", "content://sms"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True
        )
        output = result.stdout if result.stdout else "⚠️ No SMS logs found."
    except Exception as e:
        output = f"⚠️ Failed to extract SMS logs: {str(e)}"
    print("🔍 STDOUT:\n", output)
    with open("logs/sms_logs.txt", "w", encoding="utf-8") as f:
        f.write(output)

def monitor_logs(callback):
    """
    Continuously monitor logs from 'adb logcat -v time'
    and call the provided callback for each line.
    Added error-handling to avoid crashes if the callback fails.
    """
    process = subprocess.Popen(
        ['adb', 'logcat', '-v', 'time'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    try:
        while True:
            line = process.stdout.readline()
            if not line:
                # Means process ended or no device output
                break
            try:
                callback(line.rstrip('\n'))
            except Exception as cb_e:
                print("Error in callback:", cb_e)
            # Sleep briefly to avoid CPU hogging
            time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print("Error in monitor_logs:", e)
    finally:
        try:
            process.terminate()
        except Exception as term_e:
            print("Error terminating process:", term_e)
