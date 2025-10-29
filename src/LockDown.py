from os import path as ospath, makedirs, remove, environ
from time import sleep

# from elevate import elevate
from collections import deque
# from elevater import run_elevate
from lock_down_utils import get_lock_kiosk_status, duplicate_file, run_if_not_running, run_elevated, is_crash_loop
import variables as v

# ---------------- CONFIG ----------------
APP_DIR = v.APP_DIR   # app install dir (read-only)
LOG_FILE = v.LOG_FILE
FLAG_DESTRUCT_FILE = v.FLAG_DESTRUCT_FILE

lock_status = get_lock_kiosk_status()
MAIN_SCRIPT = v.MAIN_SCRIPT

# # ELEVATE_SCRIPT = path.join(path.dirname(path.abspath(__file__)), 'elevater.py')

UPDATER_SCRIPT = v.UPDATER_SCRIPT
UPDATER_SCRIPT_COPY = v.UPDATER_SCRIPT_COPY

# ---------------- FUNCTIONS ----------------
def check_files():

    if not ospath.exists(MAIN_SCRIPT):
        return False, f"Start file doesn't exists\nCannot find {MAIN_SCRIPT}"

    """Check that the log file is writable and that its drive has at least 1GB free"""
    print("Checking Log file: ", LOG_FILE)
    folder = ospath.dirname(LOG_FILE)

    # Ensure folder exists
    makedirs(folder, exist_ok=True)

    # Check writable
    try:
        with open(LOG_FILE, "a") as f:
            f.write("")  # just a test append
    except Exception as e:
        from tkinter import messagebox
        messagebox.showerror("Error", f"Log file {LOG_FILE} is not writable.\n"
                                      f"Please contact the administrator.\n\n"
                                      f"{e}")
        return False, f"Log file {LOG_FILE} is not writable"

    # Check free space
    from shutil import disk_usage
    total, used, free = disk_usage(folder)
    if free < 1 * 1024 * 1024 * 1024:  # 1 GB
        return False, f"Not enough free space ({free / (1024**3):.2f} GB available)"

    return True, ""

def clean_destruction(msg):
    print(f"Destruct flag detected, {msg}.")
    remove(FLAG_DESTRUCT_FILE)

# ---------------- LAUNCHER ----------------

def emergency_update():
    print("[!] Detected crash loop — running emergency update")
    duplicate_file(UPDATER_SCRIPT, UPDATER_SCRIPT_COPY)
    run_if_not_running(UPDATER_SCRIPT_COPY, is_background=True, arg=APP_DIR)
    sleep(20)


def run_kiosk():

    if not bool(lock_status["ENABLED"]):
        print(lock_status)
        print("Disabled on server")
        sleep(3)
        return
    
    # if not check_admin(LOCKDOWN_FILE_NAME):
    #     try:
    #         # run_if_not_running(path=ELEVATE_SCRIPT, arg=LOCKDOWN_SCRIPT)
    #         self = f'python {LOCKDOWN_SCRIPT}' if LOCKDOWN_SCRIPT.endswith('py') else LOCKDOWN_SCRIPT
    #         run_elevate('Administrator','iamadmin',False, self)
    #     except Exception as e:
    #         print(e)

    #     sleep(3)
    #     if is_admin_instance_running(LOCKDOWN_FILE_NAME):
    #         print(f"Admin {LOCKDOWN_FILE_NAME} detected. Exiting...")
    #         sys.exit(0)
        

    if ospath.exists(FLAG_DESTRUCT_FILE):
        clean_destruction("app may have crashed")

    # Pre-check folder and disk
    ok, msg = check_files()
    if not ok:
        from tkinter import messagebox, Tk
        root = Tk()
        root.withdraw()  # hide main window
        messagebox.showwarning("Launcher Warning", f"Cannot start kiosk:\n\n{msg}")
        return
    
    LOOP_HISTORY = deque(maxlen=5)
    while True:
        # Exit if destruct flag exists
        if ospath.exists(FLAG_DESTRUCT_FILE):
            clean_destruction("stopping launcher.")
            break

        try:
            if is_crash_loop(loop_history=LOOP_HISTORY, threshold=5, interval=5):
                emergency_update()
                return

            # Replace the copy every time to ensure fresh
            duplicate_file(UPDATER_SCRIPT, UPDATER_SCRIPT_COPY) 
            run_elevated(f'{UPDATER_SCRIPT_COPY} {APP_DIR} {environ.get("USERNAME")}')
            # run_if_not_running(UPDATER_SCRIPT_COPY, is_background=True, arg=ospath.join(APP_DIR, '..'))
            run_if_not_running([MAIN_SCRIPT])
            print("Next loop")

        except Exception as e:
            print(f"Error running kiosk: {e}")
            # Emergency update
            emergency_update()
            return

        # Short delay before restarting
        sleep(0.25)

# ---------------- RUN ----------------
if __name__ == "__main__":
    run_kiosk()
