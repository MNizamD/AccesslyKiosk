import os
import socket
import sys

def get_app_base_dir(sys = sys):
    """
    Return the directory that contains the running application.
    Works for:
      - dev mode (python script): returns folder of this .py file
      - frozen mode (PyInstaller one-dir or one-file): returns folder of the exe
    """
    if getattr(sys, "frozen", False):
        # Frozen by PyInstaller: sys.executable -> path to the running .exe
        return os.path.dirname(sys.executable)
    else:
        # Running as plain python script
        return os.path.dirname(os.path.abspath(__file__))

def app_name(name: str):
    if getattr(sys, "frozen", False):
        return f"{name}.exe"
    return f"{name}.py"

BASE_DIR = get_app_base_dir()
# LOCALDATA = os.getenv("LOCALAPPDATA")
PROGRAMDATA = os.getenv("PROGRAMDATA")
APP_DIR = get_app_base_dir()
TEMP = os.getenv("TEMP")
DATA_DIR = os.path.join(PROGRAMDATA, "NizamLab", "data")
CACHE_DIR = os.path.join(PROGRAMDATA, "NizamLab", "cache")   # data dir (writable)
# Ensure directory exists
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
# DATA_DIR = os.path.join(LOCALDATA, "NizamLab")   # data dir (writable)

STUDENT_CSV = os.path.join(DATA_DIR, "Students.csv")
LOG_FILE = os.path.join(DATA_DIR, "StudentLogs.csv")
FLAG_DESTRUCT_FILE = os.path.join(DATA_DIR, "STOP_LAUNCHER.flag")
FLAG_IDLE_FILE = os.path.join(DATA_DIR, "IDLE.flag")
CACHE_FILE = os.path.join(CACHE_DIR, "lock_kiosk_status.json")

LOCKDOWN_FILE_NAME = app_name("LockDown")
LOCKDOWN_SCRIPT = os.path.join(APP_DIR, LOCKDOWN_FILE_NAME)

MAIN_FILE_NAME = app_name("Main")
MAIN_SCRIPT = os.path.join(APP_DIR, MAIN_FILE_NAME)

# ELEVATE_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'elevater.py')
UPDATER_SCRIPT = os.path.join(APP_DIR, app_name("Updater"))
UPDATER_SCRIPT_COPY = os.path.join(TEMP, app_name("Updater_copy"))

CMD_SCRIPT = app_name("cmd")

DETAILS_FILE = os.path.join(APP_DIR, "details.json")
DETAILS_FILE_COPY = os.path.join(TEMP, "details.json")

PC_NAME = socket.gethostname()