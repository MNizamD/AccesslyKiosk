import sys
import os
import time
import shutil
# from elevate import elevate
from collections import deque
from tkinter import messagebox, Tk
from lock_down_utils import get_lock_kiosk_status, is_admin_instance_running, run_if_not_running, duplicate_file, is_crash_loop, check_admin, app_name

def get_app_base_dir():
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

# ---------------- CONFIG ----------------
# PROGRAM_FILES = os.environ.get("ProgramFiles", "C:\\Program Files")
# PROGRAM_DATA = os.environ.get("ProgramData", "C:\\ProgramData")
LOCALDATA = os.getenv("LOCALAPPDATA")

APP_DIR = get_app_base_dir()   # app install dir (read-only)
DATA_DIR = os.path.join(LOCALDATA, "NizamLab")   # data dir (writable)

LOG_FILE = os.path.join(DATA_DIR, "StudentLogs.csv")
FLAG_DESTRUCT_FILE = os.path.join(DATA_DIR, "STOP_LAUNCHER.flag")
FLAG_IDLE_FILE = os.path.join(DATA_DIR, "IDLE.flag")

# ### --- Load details.json ---
# DETAILS_FILE = os.path.join(BASE_DIR, "details.json")
# DETAILS_INFO = {}
# if os.path.exists(DETAILS_FILE):
#     try:
#         with open(DETAILS_FILE, "r") as f:
#             DETAILS_INFO = json.load(f)
#     except Exception as e:
#         print("Error reading details.json:", e)
# # ===========================================

lock_status = get_lock_kiosk_status()

LOCKDOWN_FILE_NAME = app_name("LockDown")
LOCKDOWN_SCRIPT = os.path.join(APP_DIR, LOCKDOWN_FILE_NAME)

MAIN_FILE_NAME = app_name("Main")
MAIN_SCRIPT = os.path.join(APP_DIR, MAIN_FILE_NAME)

ELEVATE_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'elevater.py')

UPDATER_SCRIPT = os.path.join(APP_DIR, app_name("Updater"))
UPDATER_SCRIPT_COPY = os.path.join(DATA_DIR, app_name("Updater_copy"))
DETAILS_FILE = os.path.join(APP_DIR, "details.json")
DETAILS_FILE_COPY = os.path.join(DATA_DIR, "details.json")

# ---------------- FUNCTIONS ----------------
def check_files():

    if not os.path.exists(MAIN_SCRIPT):
        return False, f"Start file doesn't exists\nCannot find {MAIN_SCRIPT}"

    """Check that the log file is writable and that its drive has at least 1GB free"""
    print("Checking Log file: ", LOG_FILE)
    folder = os.path.dirname(LOG_FILE)

    # Ensure folder exists
    os.makedirs(folder, exist_ok=True)

    # Check writable
    try:
        with open(LOG_FILE, "a") as f:
            f.write("")  # just a test append
    except Exception as e:
        messagebox.showerror("Error", f"Log file {LOG_FILE} is not writable.\n"
                                      f"Please contact the administrator.\n\n"
                                      f"{e}")
        return False, f"Log file {LOG_FILE} is not writable"

    # Check free space
    total, used, free = shutil.disk_usage(folder)
    if free < 1 * 1024 * 1024 * 1024:  # 1 GB
        return False, f"Not enough free space ({free / (1024**3):.2f} GB available)"

    return True, ""

def clean_destruction(msg):
    print(f"Destruct flag detected, {msg}.")
    os.remove(FLAG_DESTRUCT_FILE)

# ---------------- LAUNCHER ----------------

def emergency_update():
    print("[!] Detected crash loop — running emergency update")
    duplicate_file(UPDATER_SCRIPT, UPDATER_SCRIPT_COPY)
    run_if_not_running(UPDATER_SCRIPT_COPY, is_background=True, arg=APP_DIR)
    time.sleep(20)


def run_kiosk():

    # if not bool(lock_status["ENABLED"]):
    #     print(lock_status)
    #     print("Disabled on server")
    #     time.sleep(3)
    #     return
    
    if not check_admin(LOCKDOWN_FILE_NAME):
        try:
            run_if_not_running(path=ELEVATE_SCRIPT, arg=LOCKDOWN_SCRIPT)
        except Exception as e:
            print(e)

        time.sleep(3)
        if is_admin_instance_running(LOCKDOWN_FILE_NAME):
            print(f"Admin {LOCKDOWN_FILE_NAME} detected. Exiting...")
            sys.exit(0)
        

    if os.path.exists(FLAG_DESTRUCT_FILE):
        clean_destruction("app may have crashed")

    # Pre-check folder and disk
    ok, msg = check_files()
    if not ok:
        root = Tk()
        root.withdraw()  # hide main window
        messagebox.showwarning("Launcher Warning", f"Cannot start kiosk:\n\n{msg}")
        return
    
    LOOP_HISTORY = deque(maxlen=5)
    while True:
        # Exit if destruct flag exists
        if os.path.exists(FLAG_DESTRUCT_FILE):
            clean_destruction("stopping launcher.")
            break

        try:
            if is_crash_loop(loop_history=LOOP_HISTORY, threshold=5, interval=5):
                emergency_update()
                return

            # Replace the copy every time to ensure fresh
            duplicate_file(UPDATER_SCRIPT, UPDATER_SCRIPT_COPY)

            run_if_not_running(UPDATER_SCRIPT_COPY, is_background=True, arg=APP_DIR)
            run_if_not_running(MAIN_SCRIPT)
            print("Next loop")

        except Exception as e:
            print(f"Error running kiosk: {e}")
            # Emergency update
            emergency_update()
            return

        # Short delay before restarting
        time.sleep(0.25)

# ---------------- RUN ----------------
if __name__ == "__main__":
    run_kiosk()
