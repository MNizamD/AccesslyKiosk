import psycopg2
import psutil
import os
import subprocess
import shutil
import tempfile
import time
import os
import json
import ctypes
import time
from collections import deque

# Track recent loop times
# LOOP_HISTORY = deque(maxlen=5)  # keep timestamps of last 5 loops

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

def run_foreground(path):
    """Run a process in the foreground (blocking)."""
    if path.lower().endswith(".py"):
        subprocess.run(["python.exe", path])
    elif path.lower().endswith(".exe"):
        subprocess.run([path])
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
            run_foreground(path)
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


LOCALDATA = os.getenv("LOCALAPPDATA")
DATA_DIR = os.path.join(LOCALDATA, "NizamLab")   # data dir (writable)
CACHE_FILE = os.path.join(DATA_DIR, "lock_kiosk_status.json")
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
        with open(CACHE_FILE, "w") as f:
            json.dump(lock_status, f)

        cur.close()
        conn.close()
        return lock_status
    except psycopg2.OperationalError as e:
        print(f"Fetching failed: {e}")

        # Try reading from cache
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r") as f:
                    return json.load(f)
            except Exception as read_err:
                print(f"Cache read error: {read_err}")

        # Default fallback
        return {"ENABLED": True}

def check_admin(name: str):
    """Check if the script is running as root."""
    if ctypes.windll.shell32.IsUserAnAdmin() != 0:
        print(f"{name} is elevated as admin")
    else:
        print("Running as standard user")

if __name__ == "__main__":
    print(get_lock_kiosk_status()) # Test