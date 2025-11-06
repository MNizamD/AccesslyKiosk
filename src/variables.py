from os import path as ospath, getenv

def get_cur_user():
    from os import environ
    return environ.get("USERNAME")

ONLY_USER = "GVC"
PROJECT_NAME = 'NizamLab'
SCHTASK_NAME = 'AccesslyKiosk'
LOCALDATA = getenv("LOCALAPPDATA")
LOCALDATA_DIR = ospath.join(LOCALDATA, PROJECT_NAME)
TEMP = getenv("TEMP")

def is_dir_safe(path: str, user: str = get_cur_user()) -> bool:
    """
    Returns True if the given path is considered safe for app use.
    Expands environment variables (like %TEMP%) and checks that:
      - It's not inside critical system directories.
      - Specific exemption paths are allowed even if under unsafe dirs.
    """
    from os import environ

    # Expand %VAR% and ~
    normalized = normalize_path(path)

    # Define unsafe roots
    unsafe_dirs = [
        environ.get("windir", r"C:\Windows").lower(),
        "%localappdata%",
        "%programdata%",
        f"C:\\Users\\{user}",
        r"c:\windows",
        r"c:\program files",
        r"c:\program files (x86)",
        r"c:\users\default",
        r"c:\users\public\desktop",
        r"c:\$recycle.bin",
        r"c:\system volume information"
    ]

    # Define exemptions (safe exceptions)
    exemptions = [
        rf"%programdata%\{PROJECT_NAME}",
        rf"%temp%\{PROJECT_NAME}",
        rf"%localappdata%\{PROJECT_NAME}",
        f"C:\\Users\\{user}\\AppData\\Local\\{PROJECT_NAME}",
        f"C:\\Users\\{user}\\AppData\\Temp\\{PROJECT_NAME}",
    ]

    # Normalize unsafe dirs and exemptions
    normalized_unsafe = [
        normalize_path(u)
        for u in unsafe_dirs
    ]
    normalized_exemptions = [
        normalize_path(e)
        for e in exemptions
    ]

    # --- check exemptions first ---
    for ex in normalized_exemptions:
        if normalized.startswith(ex):
            return True  # ✅ explicitly allowed

    # --- then check unsafe dirs ---
    for unsafe in normalized_unsafe:
        if normalized.startswith(unsafe):
            print(f"[BLOCKED]:", normalized)
            return False  # ❌ blocked

    # Prevent root or drive root usage (like C:\)
    drive, _ = ospath.splitdrive(normalized)
    if normalized.strip("\\/") == drive.strip("\\/").lower():
        print(f"[BLOCKED]:", normalized)
        return False

    return True

def normalize_path(path: str):
    return ospath.normpath( ospath.expandvars(ospath.expanduser(path)) ).lower()

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
    if not is_dir_safe(data_dir):
        return None
    makedirs(data_dir, exist_ok=True)
    return data_dir

def CACHE_DIR():
    from os import makedirs
    cache_dir = ospath.join(LOCALDATA_DIR, "cache")
    if not is_dir_safe(cache_dir):
        return None
    makedirs(cache_dir, exist_ok=True)
    return cache_dir

def TEMP_DIR():
    from os import makedirs
    temp_dir = ospath.join(TEMP,PROJECT_NAME)
    if not is_dir_safe(temp_dir):
        return None
    makedirs(temp_dir, exist_ok=True)
    return temp_dir

STUDENT_CSV = ospath.join(DATA_DIR(), "Students.csv")
LOG_FILE = ospath.join(DATA_DIR(), "StudentLogs.csv")
FLAG_DESTRUCT_FILE = ospath.join(TEMP_DIR(), "STOP_LAUNCHER.flag")
FLAG_IDLE_FILE = ospath.join(TEMP_DIR(), "IDLE.flag")
CACHE_FILE = ospath.join(CACHE_DIR(), "lock_kiosk_status.json")

ACCESSLY_FILE_NAME = app_name("Accessly")
ACCESSLY_SCRIPT = ospath.join(APP_DIR, ACCESSLY_FILE_NAME)

MAIN_FILE_NAME = app_name("Main")
MAIN_SCRIPT = ospath.join(APP_DIR, MAIN_FILE_NAME)

# ELEVATE_SCRIPT = ospath.join(ospath.dirname(ospath.abspath(__file__)), 'elevater.py')
UPDATER_FILE_NAME = app_name("Updater")
UPDATER_COPY_FILE_NAME = app_name("Updater_copy")
UPDATER_SCRIPT = ospath.join(APP_DIR, UPDATER_FILE_NAME)
UPDATER_SCRIPT_COPY = ospath.join(TEMP, UPDATER_COPY_FILE_NAME)

CLI_NAME = app_name("cli")
CLI_SCRIPT = ospath.join(APP_DIR, CLI_NAME)

ELEVATER_NAME = app_name("elevater")
ELEVATER_SCRIPT = ospath.join(APP_DIR, ELEVATER_NAME)

DETAILS_FILE = ospath.join(APP_DIR, "details.json")
# DETAILS_FILE_COPY = ospath.join(TEMP, "details.json")

APP_PROCESSES_NAMES = [ACCESSLY_FILE_NAME, UPDATER_FILE_NAME, UPDATER_COPY_FILE_NAME, MAIN_FILE_NAME]

def PC_NAME():
    from socket import gethostname
    return gethostname()

if __name__ == "__main__":
    print(APP_DIR)