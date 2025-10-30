from os import path as ospath, getenv

def is_frozen(sys):
    return getattr(sys, "frozen", False)

def get_run_dir(sys):
    """
    Return the directory that contains the running application.
    Works for:
      - dev mode (python script): returns folder of this .py file
      - frozen mode (PyInstaller one-dir or one-file): returns folder of the exe
    """
    if is_frozen(sys):
        # Frozen by PyInstaller: sys.executable -> path to the running .exe
        return ospath.dirname(sys.executable)
    else:
        # Running as plain python script
        return ospath.dirname(ospath.abspath(__file__))

def app_name(name: str):
    import sys
    if is_frozen(sys):
        return f"{name}.exe"
    return f"{name}.py"

def move_up_dir(directory: str, level: int = 1):
    if directory is None:
        print("No directory to move up")
        return None
    return ospath.abspath(ospath.join(directory, *[".."] * level))

PROJECT_NAME = 'NizamLab'
SCHTASK_NAME = 'LockDownKiosk'
LOCALDATA = getenv("LOCALAPPDATA")
LOCALDATA_DIR = ospath.join(LOCALDATA, PROJECT_NAME)
TEMP = getenv("TEMP")

# PROGRAMDATA = getenv("PROGRAMDATA")
# BASE_DIR = PROGRAMDATA
def RUN_DIR():
    import sys
    return get_run_dir(sys)
# RUN_DIR = get_run_dir(getsys())
BASE_DIR = move_up_dir(RUN_DIR())
APP_DIR = ospath.join(BASE_DIR, 'src')
def DATA_DIR():
    from os import makedirs
    data_dir = ospath.join(LOCALDATA_DIR, "data")
    makedirs(data_dir, exist_ok=True)
    return data_dir

def CACHE_DIR():
    from os import makedirs
    cache_dir = ospath.join(LOCALDATA_DIR, "cache")
    makedirs(cache_dir, exist_ok=True)
    return cache_dir

def TEMP_DIR():
    from os import makedirs
    temp_dir = ospath.join(TEMP,PROJECT_NAME)
    makedirs(temp_dir, exist_ok=True)
    return temp_dir

STUDENT_CSV = ospath.join(DATA_DIR(), "Students.csv")
LOG_FILE = ospath.join(DATA_DIR(), "StudentLogs.csv")
FLAG_DESTRUCT_FILE = ospath.join(TEMP_DIR(), "STOP_LAUNCHER.flag")
FLAG_IDLE_FILE = ospath.join(TEMP_DIR(), "IDLE.flag")
CACHE_FILE = ospath.join(CACHE_DIR(), "lock_kiosk_status.json")

LOCKDOWN_FILE_NAME = app_name("LockDown")
LOCKDOWN_SCRIPT = ospath.join(APP_DIR, LOCKDOWN_FILE_NAME)

MAIN_FILE_NAME = app_name("Main")
MAIN_SCRIPT = ospath.join(APP_DIR, MAIN_FILE_NAME)

# ELEVATE_SCRIPT = ospath.join(ospath.dirname(ospath.abspath(__file__)), 'elevater.py')
UPDATER_SCRIPT = ospath.join(APP_DIR, app_name("Updater"))
UPDATER_SCRIPT_COPY = ospath.join(TEMP, app_name("Updater_copy"))

CMD_NAME = app_name("cmd")
CMD_SCRIPT = ospath.join(APP_DIR, CMD_NAME)

ELEVATER_NAME = app_name("elevater")
ELEVATER_SCRIPT = ospath.join(APP_DIR, ELEVATER_NAME)

DETAILS_FILE = ospath.join(RUN_DIR(), "details.json")
# DETAILS_FILE_COPY = ospath.join(TEMP, "details.json")

def PC_NAME():
    from socket import gethostname
    return gethostname()

if __name__ == "__main__":
    print(APP_DIR)