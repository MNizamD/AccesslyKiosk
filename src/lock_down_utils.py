from os import path as ospath, makedirs, remove as rm, getlogin, getpid
from collections import deque
from variables import CACHE_FILE, DETAILS_FILE, APP_DIR
# import request

CACHE_FILE = CACHE_FILE
DETAILS_FILE = DETAILS_FILE

def is_crash_loop(loop_history: deque, threshold=5, interval=1.0):
    """
    Detects if the loop is repeating too fast (e.g., crashes).
    - threshold: how many loops inside 'window' seconds trigger crash detection
    - window: time in seconds
    """
    from time import time
    now = time()
    loop_history.append(now)

    # Keep only the most recent `threshold` timestamps
    while len(loop_history) > threshold:
        loop_history.popleft()

    # If we have enough samples, check time difference
    if len(loop_history) == loop_history.maxlen:
        # oldest vs newest in history
        duration = loop_history[-1] - loop_history[0]
        if duration < interval:
            return True
    return False


def is_process_running(name: str) -> bool:
    from psutil import process_iter, NoSuchProcess, AccessDenied
    """Check if a process with given name is already running"""
    for proc in process_iter(attrs=["name"]):
        try:
            if proc.info["name"].lower() == name.lower():
                return True
        except (NoSuchProcess, AccessDenied):
            continue
    return False

def run_background(cmd: list):
    from tempfile import gettempdir
    from subprocess import Popen, DETACHED_PROCESS, CREATE_NEW_PROCESS_GROUP
    """Run a process in the background (non-blocking)."""
    path = cmd[0]
    if ospath.exists(path):
        Popen(
            cmd,
            cwd=gettempdir(),     # run outside NizamLab
            creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
            close_fds=True
        )
    else:
        print(f"[WARN] {path} not found")

# def get_process_args(argv):
#     if len(argv) > 1:
#         return argv[1:]
#     return None

# def run_foreground(cmd: list):
#     """Run a process in the foreground (blocking)."""
#     from subprocess import run
#     # if any(path.lower().endswith(res) for res in [".exe", ".py", ".cmd"]):
#     run(cmd)
#     # else:
#     #     print(f"[WARN] Unknown file type: {path}")

def run_if_not_running(cmd: list, is_background = False):
    """Run an exe if not already running"""
    path = cmd[0]
    exe_name = ospath.basename(path)
    if path.lower().endswith(".py"):
        python = find_python_exe()
        if python is None:
            return None
        cmd.insert(0, python)

    if not ospath.exists(path):
        print(f"[WARN] {exe_name} not found at {path}")
        return None
    if not is_process_running(exe_name):
        print(f"[INFO] Starting {exe_name}...")
        if is_background == True:
            run_background(cmd)
        else:
            from subprocess import run
            # run_foreground(cmd)
            run(cmd)
    else:
        print(f"[INFO] {exe_name} already running.")
    return None

def kill_processes(names):
    from time import sleep
    from psutil import process_iter, NoSuchProcess
    for n in names:
        for proc in process_iter(["name"]):
            try:
                if proc.info["name"].lower() == n.lower():
                    proc.kill()
                    sleep(3)
            except NoSuchProcess:
                pass

def duplicate_file(src:str, cpy:str):
    try:
        if ospath.exists(cpy):
            rm(cpy)
        from shutil import copy2
        copy2(src, cpy)
    except Exception as e:
        print(f"Duplication error: {e}")

def get_lock_kiosk_status() -> dict:
    from psycopg2 import connect, OperationalError
    try:
        # Connect with your Supabase Postgres URI
        conn = connect(
            "postgresql://postgres.wfnhabdtwcjebmyeglnt:qOe8OeQoGqOhQJia@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres",
            sslmode="require"
        )
        cur = conn.cursor()

        # Fetch all rows (assuming table has columns: key, value)
        cur.execute("SELECT key, value FROM lock_kiosk_status WHERE deleted_at is NULL;")
        rows = cur.fetchall()

        # Convert to dictionary
        lock_status = {key: value for key, value in rows}

        # Save to file (cache)
        write_json(CACHE_FILE, lock_status)

        cur.close()
        conn.close()
        return lock_status
    except OperationalError as e:
        print(f"Fetching failed: {e}")

        # Try reading from cache
        if ospath.exists(CACHE_FILE):
            result = read_json(CACHE_FILE)
            if result != None:
                return result
        
        # No cache file, write new one
        write_json(CACHE_FILE, {"ENABLED": True})

        # Default fallback
        return {"ENABLED": True}

def read_json(file: str):
    from json import load
    try:
        with open(file, "r") as f:
            return load(f)
    except Exception as read_err:
        print(f"JSON read error: {read_err}")
        return None
    
def write_json(file: str, value):
    from json import dump
    # Ensure parent folder exists
    makedirs(ospath.dirname(file), exist_ok=True)
    
    # Create or overwrite the file
    with open(file, "w") as f:
        dump(value, f, indent=4)

def check_admin(name: str):
    from ctypes import windll
    """Check if the script is running as root."""
    if windll.shell32.IsUserAnAdmin() != 0:
        print(f"{name} is elevated as admin")
        return True
    else:
        print(f"{name} is running as standard user")
        return False

def find_python_exe():
    from sys import executable
    from shutil import which
    """Return full path to a python.exe to use, or None if not found."""
    # 1) if running under a python interpreter (non-frozen), use it
    exe = executable
    if exe and ospath.basename(exe).lower().startswith("python"):
        print("Python interpreter found")
        return exe

    # 2) try 'python' on PATH
    py_on_path = which("python")
    if py_on_path:
        print("Python environment found")
        return py_on_path

    # 3) try the python launcher 'py'
    py_launcher = which("py")
    if py_launcher:
        # prefer py -3 if available (we want an exe path, but py is a launcher)
        print("Python launcher PY found")
        return py_launcher
    
    # 4) common per-user and system-wide installs
    common_dirs = [
        rf"C:\Users\{getlogin()}\AppData\Local\Programs\Python",
        r"C:\Program Files",
        r"C:\Program Files (x86)",
        r"C:\Users\{getlogin()}\anaconda3",
        r"C:\Users\{getlogin()}\miniconda3",
    ]
    from glob import glob
    for base in common_dirs:
        if ospath.isdir(base):
            for exe_path in glob.glob(ospath.join(base, "Python*", "python.exe")):
                print("Python common directory found")
                return exe_path
    
    return None
    # 5) fallback: look for a portable python in temp (you must place it there beforehand)
#     temp = tempfile.gettempdir()
#     py_dir = ospath.join(temp, "portable_python")
#     temp_python = ospath.join(py_dir, "python.exe")
#     if not ospath.exists(temp_python):
#         print("Downloading portable Python...")
#         url = "https://www.python.org/ftp/python/3.12.5/python-3.12.5-embed-amd64.zip"
#         zip_path = ospath.join(temp, "py.zip")
#         if not download(url, zip_path):
#             print("Something went wrong :(")
#         else:
#             print("Download portable python complete!")

#         with zipfile.ZipFile(zip_path, "r") as zf:
#             zf.extractall(py_dir)
#     # Embedded Python disables site-packages by default
#     pth_files = [f for f in os.listdir(py_dir) if f.endswith("._pth")]
#     if pth_files:
#         pth_file = ospath.join(py_dir, pth_files[0])
#         with open(pth_file, "r") as f:
#             lines = f.readlines()
#         with open(pth_file, "w") as f:
#             for line in lines:
#                 # Uncomment "import site" to enable site-packages
#                 if line.strip() == "#import site":
#                     f.write("import site\n")
#                 else:
#                     f.write(line)
#         print(f"Fixed _pth file: {pth_file}")
        
#     if ospath.exists(temp_python):
#         print("Python portable found")

    
#     return temp_python

def download(src: str, dst: str):
    from requests import get
    try:
        with get(src, stream=True) as r:
            r.raise_for_status()
            with open(dst, "wb") as f:
                for chunk in r.iter_content(8192):
                    if chunk:
                        f.write(chunk)
        return True
    except Exception as e:
        print("[ERR_DOWNLOAD]:", e)
        return False

def is_admin_instance_running(exe_name: str):
    from psutil import process_iter, Process, AccessDenied, NoSuchProcess, ZombieProcess
    """Check if another process with the same exe name is running as admin."""
    current_pid = getpid()

    for proc in process_iter(['pid', 'name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() == exe_name.lower():
                if proc.info['pid'] == current_pid:
                    continue  # skip self
                
                # Try checking if the process runs as admin
                # Open with limited rights (no crash if not admin)
                handle = Process(proc.info['pid'])
                try:
                    if handle.username().lower().endswith('\\administrator'):
                        return True
                except AccessDenied:
                    # AccessDenied usually means it's a higher-privilege process (admin)
                    return True
        except (NoSuchProcess, ZombieProcess):
            continue

    return False

# ================= Utility ====================
def get_details_json():
    from json import load
    try:
        path = ospath.join(APP_DIR, DETAILS_FILE)
        if not ospath.exists(path):
            raise FileNotFoundError(f"Missing file: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return load(f)

    except Exception as e:
        print("[GET_DETAILS_JSON_ERR]:", e)
        return {"version": "?", "updated": "?"}


def run_elevated(cmd: str):
    from elevater import run_elevate
    run_elevate('Administrator','iamadmin', False, cmd)

if __name__ == "__main__":
    print(get_lock_kiosk_status()) # Test