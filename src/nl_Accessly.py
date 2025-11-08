from time import sleep
from lib_env import get_env, get_current_executable_name
from sys import exit, argv
from lib_util import showToFronBackEnd

env = get_env()

# ---------------- CONFIG ----------------
LOG_FILE = env.log_file

UPDATER_SCRIPT = env.script_updater
UPDATER_SCRIPT_COPY = env.script_updater_copy
MAIN_SCRIPT = env.script_main

# ---------------- FUNCTIONS ----------------
def check_server() -> bool:
    from lib_util import get_accessly_status
    lock_status = get_accessly_status(env=env)
    if bool(lock_status["ENABLED"]) == False:
        raise Exception("Disabled on server.")
    return True

def check_files() -> bool:

    if not MAIN_SCRIPT.exists():
        raise Exception(f"Cannot find {MAIN_SCRIPT}.") 

    """Check that the log file is writable and that its drive has at least 1GB free"""
    print("Checking Log file: ", LOG_FILE)
    # Check writable
    try:
        with open(LOG_FILE, "a") as f:
            f.write("")  # just a test append
    except Exception as e:
        raise Exception(f"Log file is not writable {LOG_FILE}\n\n{e}")

    # Check free space
    from shutil import disk_usage
    total, used, free = disk_usage(env.data_dir)
    if free < 1 * 1024 * 1024 * 1024:  # 1 GB
        raise Exception(f"Not enough free space ({free / (1024**3):.2f} GB available)")

    return True

# ---------------- LAUNCHER ----------------
def run_updater(force: bool = False):
    from lib_util import duplicate_file, run_elevated
    force_arg = '' if not force else '--force'
    if duplicate_file(UPDATER_SCRIPT, UPDATER_SCRIPT_COPY):
        run_elevated(f'{UPDATER_SCRIPT_COPY} --dir {env.base_dir} --user "{env.user}" {force_arg}')
    else:
        showToFronBackEnd(title="Updater", msg="Failed to duplicate updater.")

def emergency_update():
    showToFronBackEnd("Crash","Detected crash loop!\nRunning emergency update...")
    run_updater(force=True)
    sleep(20)
    exit(1)


def run_kiosk():
    check_server()
    check_files()
    run_updater()
    from lib_util import run_normally, is_crash_loop, kill_processes
    from os import path as ospath
    
    from collections import deque
    LOOP_HISTORY = deque(maxlen=5)
    while True:
        exitcode = run_normally([str(MAIN_SCRIPT)], wait=True)
        if exitcode == 0:
            print("Main ended successfully.")
            break # App closed successfully

        if exitcode == 369:
            print("Main encountered errors.") # App encountered error
        
        # App did not properly
        if is_crash_loop(loop_history=LOOP_HISTORY, threshold=5, window=15):
            kill_processes(env.all_app_processes(), False)
            emergency_update()
        
        # Short delay before restarting
        sleep(0.25)

# ---------------- RUN ----------------
if __name__ == "__main__":
    try:
        if '--emergency' in argv:
            emergency_update()
            
        from lib_util import raise_if_task_running, kill_processes
        raise_if_task_running(get_current_executable_name())
        # Kill all running app
        kill_processes(env.all_app_processes()) # Drop the accessly's name
        run_kiosk()
    except Exception as e:
        showToFronBackEnd(title="Accessly Error", msg=f"Please contact the administrator.", details=str(e))
        exit(1)
    else:
        exit(0)
        
