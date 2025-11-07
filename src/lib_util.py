from os import path as ospath, getlogin
from collections import deque
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

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


class ProcessCheckResult:
    running: bool = False
    data: dict[str, Any] = {}
    def __init__(self, running: bool, data: Optional[dict[str, Any]] = None):
        self.running = running
        if data != None:
            self.data = data

    def __bool__(self):
        # When used in `if` statements, treat as the bool result
        return self.running

    def __iter__(self):
        # Allows unpacking like `is_running, data = result`
        yield self.running
        yield self.data


def is_process_running(name: str) -> ProcessCheckResult:
    """Check if a process with given name is already running (excluding self)."""
    from os import getpid
    current_pid = getpid()

    from psutil import process_iter, NoSuchProcess, AccessDenied
    """Check if a process with given name is already running"""
    # attrs=["pid", "name", "exe", "cmdline", "username"]
    for proc in process_iter(attrs=["pid", "name", "exe"]):
        try:
            if proc.info["pid"] == current_pid:
                continue  # skip self
            if proc.info["name"].lower() == name.lower():
                return ProcessCheckResult(True, proc.info)
        except (NoSuchProcess, AccessDenied):
            continue
    return ProcessCheckResult(False, None)


def run_background(cmd: list):
    from tempfile import gettempdir
    import subprocess
    """Run a process in the background (non-blocking)."""
    path = cmd[0]
    if ospath.exists(path):
        creationflags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        subprocess.Popen(
            cmd,
            cwd=gettempdir(),     # run outside NizamLab
            creationflags=creationflags,
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

def run_if_not_running(cmd: list[str], is_background = False):
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

def kill_processes(names: list[str], silent: bool = True):
    from time import sleep
    from psutil import process_iter, NoSuchProcess
    from os import getpid
    current_pid = getpid()
    for n in names:
        for proc in process_iter(attrs=["name", "pid"]):
            try:
                if proc.info["pid"] == current_pid:
                    continue  # skip self
                if proc.info["name"].lower() == n.lower():
                    proc.kill()
                    if not silent:
                        print(f"{n} process killed.")
                    sleep(3)
            except NoSuchProcess:
                if not silent:
                    print(f"No such process: {n}")
                pass


def duplicate_file(src:Path, cpy:Path):
    try:
        if ospath.exists(cpy):
            from os import remove
            remove(cpy)
        from shutil import copy2
        copy2(src, cpy)
    except Exception as e:
        print(f"Duplication error: {e}")

def get_accessly_status(env) -> dict:
    from psycopg2 import connect, OperationalError
    from lib_env import parse_env
    env = parse_env(env)
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
        write_json(str(env.cache_file), lock_status)

        cur.close()
        conn.close()
        return lock_status
    except OperationalError as e:
        print(f"Fetching failed: {e}")

        # Try reading from cache
        if ospath.exists(env.cache_file):
            result = read_json(str(env.cache_file))
            if result != None:
                return result
        
        # No cache file, write new one
        write_json(str(env.cache_file), {"ENABLED": True})

        # Default fallback
        return {"ENABLED": True}

def read_json(file: str) -> Optional[dict[str, Any]]:
    from json import load
    try:
        with open(file, "r") as f:
            return load(f)
    except Exception as read_err:
        print(f"JSON read error: {read_err}")
        return None
    
def write_json(file: str, value):
    from json import dump
    from os import makedirs
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
            for exe_path in glob(ospath.join(base, "Python*", "python.exe")):
                print("Python common directory found")
                return exe_path
    
    return None

def download(
        src: str,
        dst: str,
        progress_callback: Optional[Callable[[float], None]] = None
    ):
    from requests import get

    try:
        with get(src, stream=True) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            downloaded = 0

            with open(dst, "wb") as f:
                for chunk in r.iter_content(8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        # Call progress callback if provided
                        if progress_callback:
                            progress_callback(downloaded * 100 / total)

        return True

    except Exception as e:
        print("[ERR_DOWNLOAD]:", e)
        return False


def is_admin_instance_running(exe_name: str):
    from psutil import process_iter, Process, AccessDenied, NoSuchProcess, ZombieProcess
    from os import getpid
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
def get_details_json(env) -> dict[str, str] | None:
    from lib_env import parse_env
    path = parse_env(env).details_file
    from json import load
    try:
        if not ospath.exists(path):
            raise FileNotFoundError(f"Missing details: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return load(f)

    except Exception as e:
        print("[GET_DETAILS_JSON_ERR]:", e)
        return None


def run_elevated(cmd: str, wait: bool = False):
    from elevater import run_elevate
    from lib_env import is_frozen
    import sys
    pre_app = f'{find_python_exe()} ' if not is_frozen(sys=sys) else ''
    run_elevate('Administrator','iamadmin', wait, f"{pre_app}{cmd}")

if __name__ == "__main__":
    from lib_env import get_env
    print(get_accessly_status(env=get_env())) # Test
    # print(is_dir_safe(input("Directory: ")))