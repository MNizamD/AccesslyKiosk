from os import path as ospath, makedirs
from time import sleep
from lib_env import get_env, get_current_executable_name
env = get_env()

# ---------------- CONFIG ----------------
BASE_DIR = env.base_dir# app install dir (read-only)
LOG_FILE = env.log_file
FLAG_DESTRUCT_FILE = env.flag_destruct_file

UPDATER_SCRIPT = env.script_updater
UPDATER_SCRIPT_COPY = env.script_updater_copy
MAIN_SCRIPT = env.script_main

# ---------------- FUNCTIONS ----------------
def check_files():

    if not MAIN_SCRIPT.exists():
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
    if not env.is_dir_safe(FLAG_DESTRUCT_FILE):
        return
    from os import remove
    print(f"Destruct flag detected, {msg}.")
    remove(FLAG_DESTRUCT_FILE)

# ---------------- LAUNCHER ----------------
def run_updater():
    from lib_util import duplicate_file, run_elevated
    from os import environ
    duplicate_file(UPDATER_SCRIPT, UPDATER_SCRIPT_COPY) 
    run_elevated(f'{UPDATER_SCRIPT_COPY} --dir {BASE_DIR} --user {environ.get("USERNAME")}')

def emergency_update():
    print("[!] Detected crash loop — running emergency update")
    run_updater()
    sleep(20)


def run_kiosk():
    from lib_util import get_accessly_status, run_normally, is_crash_loop, kill_processes
    lock_status = get_accessly_status(env=env)
    if not bool(lock_status["ENABLED"]):
        print(lock_status)
        print("Disabled on server")
        sleep(3)
        return
    
    # if not check_admin(ACCESSLY_FILE_NAME):
    #     try:
    #         # run_if_not_running(path=ELEVATE_SCRIPT, arg=ACCESSLY_SCRIPT)
    #         self = f'python {ACCESSLY_SCRIPT}' if ACCESSLY_SCRIPT.endswith('py') else ACCESSLY_SCRIPT
    #         run_elevate('Administrator','iamadmin',False, self)
    #     except Exception as e:
    #         print(e)

    #     sleep(3)
    #     if is_admin_instance_running(ACCESSLY_FILE_NAME):
    #         print(f"Admin {ACCESSLY_FILE_NAME} detected. Exiting...")
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
    
    # Kill all running app
    kill_processes(env.all_app_processes()) # Drop the accessly's name 
    from collections import deque
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
            run_updater()
            run_normally(env=env, cmd=str(MAIN_SCRIPT), wait=True)
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
    from lib_util import is_process_running
    current_name = get_current_executable_name()
    if is_process_running(current_name):
        print(current_name,'is currently running, exiting...')
        from sys import exit
        exit(0)
    run_kiosk()
