
from os import path as ospath, getlogin
from collections import deque
from pathlib import Path
from typing import Any, Optional
from env import EnvHelper

def is_crash_loop(loop_history: deque, threshold=5, window=1.0):
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
        if duration < window:
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

def raise_if_task_running(task):
    if is_process_running(task):
        raise Exception(f"{task} is already running...")

def run_normally(cmd: list[str], wait: bool = True, hidden: bool = False) -> int:
    app = str(cmd[0])
    if app.lower().endswith('py'):
        python = find_python_exe()
        if python != None:
            cmd.insert(0, python)

    if wait:
        from subprocess import run
        return run(cmd, shell=False).returncode
    else:
        from subprocess import Popen, DEVNULL, CREATE_NO_WINDOW
        proc = Popen(
            cmd,
            shell=False,
            stdin=DEVNULL,
            stdout=None,
            stderr=None,
            creationflags=CREATE_NO_WINDOW if hidden else 0
        )
        return proc.pid

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


def duplicate_file(src:Path, cpy:Path) -> bool:
    try:
        if ospath.exists(cpy):
            from os import remove
            remove(cpy)
        from shutil import copy2
        copy2(src, cpy)
    except Exception as e:
        print(f"Duplication error: {e}")
        return False
    else:
        return True

StatusType = dict[str, Any]
def get_accessly_status(env: EnvHelper) -> StatusType:
    def get_cache() -> StatusType:
        if ospath.exists(env.cache_file):
            result = read_json(str(env.cache_file))
            if result != None:
                return result
            
        # No cache file, write new one and fallback
        cache = {"ENABLED": True}
        write_json(str(env.cache_file), cache)
        return cache

    try:
        from conn import fetch_database
        lock_status = fetch_database(
            select_=["key", "value"],
            from_="lock_kiosk_status",
            where_="deleted_at is NULL"
        )

        from tool import find_dict
        is_enabled = find_dict(data=lock_status or [], key='key', value='ENABLED')
        if is_enabled is None:
            raise FileNotFoundError("Could not find accessly status")
        
        result = { 'ENABLED': is_enabled['value'] }
        # Save to file (cache)
        write_json(str(env.cache_file), result)
        return result
    except Exception as e:
        print(f"Fetching failed: {e}")
        # Try reading from cache
        return get_cache()

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
def get_details_json(env: EnvHelper) -> dict[str, str|None]:
    
    path = env.details_file
    from json import load
    try:
        if not ospath.exists(path):
            raise FileNotFoundError(f"Missing details: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return load(f)

    except Exception as e:
        print("[GET_DETAILS_JSON_ERR]:", e)
        return { "version": None, "updated": None}

def run_elevated(cmd: str, wait: bool = False):
    from lib.elevater import run_elevate
    from env import is_frozen
    import sys
    pre_app = f'{find_python_exe()} ' if not is_frozen(sys=sys) else ''
    run_elevate('Administrator','iamadmin', wait, f"{pre_app}{cmd}")

def showToFronBackEnd(title: str, msg: str, details: str = ''):
    from tkinter import messagebox
    print(f"[{title}] {msg}\n{details}")
    messagebox.showerror(title=title, message=msg, detail=details)

if __name__ == "__main__":
    from env import get_env
    import sys
    env=get_env(sys=sys)
    print(get_accessly_status(env=env)) # Test
    # print(is_dir_safe(input("Directory: ")))