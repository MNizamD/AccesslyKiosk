import glob
import zipfile
import psycopg2
import psutil
import os
import sys
import subprocess
import shutil
import tempfile
import time
import os
import json
import ctypes
import time
from collections import deque
import variables as v
import requests
from elevater import run_elevate

# Track recent loop times
# LOOP_HISTORY = deque(maxlen=5)  # keep timestamps of last 5 loops

CACHE_FILE = v.CACHE_FILE
DETAILS_FILE = v.DETAILS_FILE

def is_crash_loop(loop_history: deque, threshold=5, interval=1.0):
    """
    Detects if the loop is repeating too fast (e.g., crashes).
    - threshold: how many loops inside 'window' seconds trigger crash detection
    - window: time in seconds
    """
    now = time.time()
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
    """Check if a process with given name is already running"""
    for proc in psutil.process_iter(attrs=["name"]):
        try:
            if proc.info["name"].lower() == name.lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

def run_background(path: str, arg: str = None):
    """Run a process in the background (non-blocking)."""
    if os.path.exists(path):
        cmd = []
        if path.lower().endswith(".py"):
            cmd = ["python.exe", path]
        elif path.lower().endswith(".exe"):
            cmd = [path]

        if arg is not None:  # only append if provided
            cmd.append(str(arg))

        subprocess.Popen(
            cmd,
            cwd=tempfile.gettempdir(),     # run outside NizamLab
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
            close_fds=True
        )
    else:
        print(f"[WARN] {path} not found")

def get_process_arg(system):
    if len(system.argv) > 1:
        return system.argv[1]
    return None



def run_foreground(path: str, arg: str = None):
    """Run a process in the foreground (blocking)."""
    if path.lower().endswith(".py"):
        subprocess.run([find_python_exe(), path, arg])
    elif path.lower().endswith(".exe"):
        subprocess.run([path, arg])
    else:
        print(f"[WARN] Unknown file type: {path}")

def run_if_not_running(path: str, is_background = False, arg:str = None):
    """Run an exe if not already running"""
    exe_name = os.path.basename(path)
    if not os.path.exists(path):
        print(f"[WARN] {exe_name} not found at {path}")
        return None
    if not is_process_running(exe_name):
        print(f"[INFO] Starting {exe_name}...")
        if is_background == True:
            run_background(path, arg)
        else:
            run_foreground(path, arg)
    else:
        print(f"[INFO] {exe_name} already running.")
    return None

def kill_processes(names):
    for n in names:
        for proc in psutil.process_iter(["name"]):
            try:
                if proc.info["name"].lower() == n.lower():
                    proc.kill()
                    time.sleep(3)
            except psutil.NoSuchProcess:
                pass

def duplicate_file(src:str, cpy:str):
    try:
        if os.path.exists(cpy):
            os.remove(cpy)
        shutil.copy2(src, cpy)
    except Exception as e:
        print(f"Duplication error: {e}")

def get_lock_kiosk_status() -> dict:
    try:
        # Connect with your Supabase Postgres URI
        conn = psycopg2.connect(
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
        write_json_cache(CACHE_FILE, lock_status)

        cur.close()
        conn.close()
        return lock_status
    except psycopg2.OperationalError as e:
        print(f"Fetching failed: {e}")

        # Try reading from cache
        if os.path.exists(CACHE_FILE):
            result = read_json_cache()
            if result != None:
                return result
        
        # No cache file, write new one
        write_json_cache(CACHE_FILE, {"ENABLED": True})

        # Default fallback
        return {"ENABLED": True}

def read_json_cache(file: str):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except Exception as read_err:
        print(f"Cache read error: {read_err}")
        return None
    
def write_json_cache(file: str, value):
    # Ensure parent folder exists
    os.makedirs(os.path.dirname(file), exist_ok=True)
    
    # Create or overwrite the file
    with open(file, "w") as f:
        json.dump(value, f, indent=4)

def check_admin(name: str):
    """Check if the script is running as root."""
    if ctypes.windll.shell32.IsUserAnAdmin() != 0:
        print(f"{name} is elevated as admin")
        return True
    else:
        print(f"{name} is running as standard user")
        return False

def find_python_exe():
    """Return full path to a python.exe to use, or None if not found."""
    # 1) if running under a python interpreter (non-frozen), use it
    exe = sys.executable
    if exe and os.path.basename(exe).lower().startswith("python"):
        print("Python interpreter found")
        return exe

    # 2) try 'python' on PATH
    py_on_path = shutil.which("python")
    if py_on_path:
        print("Python environment found")
        return py_on_path

    # 3) try the python launcher 'py'
    py_launcher = shutil.which("py")
    if py_launcher:
        # prefer py -3 if available (we want an exe path, but py is a launcher)
        print("Python launcher PY found")
        return py_launcher
    
    # 4) common per-user and system-wide installs
    common_dirs = [
        rf"C:\Users\{os.getlogin()}\AppData\Local\Programs\Python",
        r"C:\Program Files",
        r"C:\Program Files (x86)",
        r"C:\Users\{os.getlogin()}\anaconda3",
        r"C:\Users\{os.getlogin()}\miniconda3",
    ]
    for base in common_dirs:
        if os.path.isdir(base):
            for exe_path in glob.glob(os.path.join(base, "Python*", "python.exe")):
                print("Python common directory found")
                return exe_path

    # 5) fallback: look for a portable python in temp (you must place it there beforehand)
    temp = tempfile.gettempdir()
    py_dir = os.path.join(temp, "portable_python")
    temp_python = os.path.join(py_dir, "python.exe")
    if not os.path.exists(temp_python):
        print("Downloading portable Python...")
        url = "https://www.python.org/ftp/python/3.12.5/python-3.12.5-embed-amd64.zip"
        zip_path = os.path.join(temp, "py.zip")
        if not download(url, zip_path):
            print("Something went wrong :(")
        else:
            print("Download portable python complete!")

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(py_dir)
    # Embedded Python disables site-packages by default
    pth_files = [f for f in os.listdir(py_dir) if f.endswith("._pth")]
    if pth_files:
        pth_file = os.path.join(py_dir, pth_files[0])
        with open(pth_file, "r") as f:
            lines = f.readlines()
        with open(pth_file, "w") as f:
            for line in lines:
                # Uncomment "import site" to enable site-packages
                if line.strip() == "#import site":
                    f.write("import site\n")
                else:
                    f.write(line)
        print(f"Fixed _pth file: {pth_file}")
        
    if os.path.exists(temp_python):
        print("Python portable found")

    
    return temp_python

def download(src: str, dst: str):
    try:
        with requests.get(src, stream=True) as r:
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
    """Check if another process with the same exe name is running as admin."""
    current_pid = os.getpid()

    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() == exe_name.lower():
                if proc.info['pid'] == current_pid:
                    continue  # skip self
                
                # Try checking if the process runs as admin
                # Open with limited rights (no crash if not admin)
                handle = psutil.Process(proc.info['pid'])
                try:
                    if handle.username().lower().endswith('\\administrator'):
                        return True
                except psutil.AccessDenied:
                    # AccessDenied usually means it's a higher-privilege process (admin)
                    return True
        except (psutil.NoSuchProcess, psutil.ZombieProcess):
            continue

    return False

# ================= Utility ====================
def get_details_json():
    APP_DIR = v.get_app_base_dir()
    try:
        path = os.path.join(APP_DIR, DETAILS_FILE)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing file: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception as e:
        print("[GET_DETAILS_JSON_ERR]:", e)
        return {"version": "?", "updated": "?"}

def move_up_dir(directory: str, level: int = 1):
    return os.path.abspath(os.path.join(directory, *[".."] * level))

def run_elevated(cmd: str):
    run_elevate('Administrator','iamadmin', False, cmd)

if __name__ == "__main__":
    print(get_lock_kiosk_status()) # Test