# config.py

# Global configuration and constants
BG_COLOR = "black"
FG_COLOR = "lime"
TEXT_BG_COLOR = "black"
TEXT_FG_COLOR = "lime"
BUTTON_COLOR = "gray"
BUTTON_TEXT_COLOR = "black"
FONT = ("Consolas", 10)

# Log types and corresponding regex patterns and colors
LOG_TYPES = {
    "Application": {
        "description": "Application-specific logs",
        "pattern": r'ActivityManager|PackageManager|ApplicationContext',
        "color": "blue"
    },
    "System": {
        "description": "System-level logs",
        "pattern": r'SystemServer|System\.err|SystemClock|SystemProperties',
        "color": "green"
    },
    "Crash": {
        "description": "Application crashes and exceptions",
        "pattern": r'FATAL|Exception|ANR|crash|force close|stacktrace',
        "color": "red"
    },
    "GC": {
        "description": "Garbage Collection events",
        "pattern": r'dalvikvm.*GC|art.*GC|GC_|collector',
        "color": "purple"
    },
    "Network": {
        "description": "Network activity logs",
        "pattern": r'ConnectivityManager|NetworkInfo|WifiManager|HttpURLConnection|socket|wifi|TCP|UDP|DNS',
        "color": "cyan"
    },
    "Broadcast": {
        "description": "Broadcast receivers and events",
        "pattern": r'BroadcastReceiver|sendBroadcast|onReceive|Intent.*broadcast',
        "color": "yellow"
    },
    "Service": {
        "description": "Service lifecycle events",
        "pattern": r'Service|startService|stopService|bindService|onBind',
        "color": "orange"
    },
    "Device": {
        "description": "Device state and hardware",
        "pattern": r'PowerManager|BatteryManager|sensor|hardware|camera|location|bluetooth|telephony',
        "color": "magenta"
    }
}

# Monitoring flag and queue (used by live-monitor module)
monitoring_active = False
log_queue = None  # Will be initialized in the main module
