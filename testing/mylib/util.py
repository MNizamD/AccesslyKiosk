import sys
from os import path as ospath, environ
from pathlib import Path
from typing import Literal, Optional

PROJECT_NAME = "NizamLab"
ONLY_USER = "GVC"

def launcher_name():
    return app_name("launcher")

def services_name():
    return app_name("services")

def app_names():
    return [ launcher_name(), services_name() ]

def get_name_from_path(path: Optional[str] = None) -> str:
    if path != None:
        return ospath.basename(path)
    
    """Return the name of the currently running file or executable."""
    if is_frozen():
        # When bundled by PyInstaller or similar
        return ospath.basename(Path(sys.executable))
    else:
        # Normal Python script
        return ospath.basename(Path(sys.argv[0]).resolve())

def move_up_dir(directory: Path, level: int = 1) -> Path:
    """
    Move up `level` directories from `directory`.
    """
    for _ in range(level):
        directory = directory.parent
    return directory.resolve()

def is_frozen():
    return getattr(sys, "frozen", False)

def is_user_exists(username: str) -> bool:
    """Check if a local Windows user exists."""
    from subprocess import run
    try:
        result = run(
            ["net", "user", username],
            capture_output=True,
            text=True,
            shell=True
        )
        # Return code 0 = user exists
        return result.returncode == 0
    except Exception as e:
        print(f"Error checking user: {e}")
        return False
    
def get_cur_user() -> str:
    return environ.get("USERNAME", "Unknown")

def get_cur_dir() -> Path:
    """Folder containing the running file or executable."""
    if is_frozen():
        return Path(sys.executable).parent
    return Path(sys.argv[0]).resolve().parent
    

def app_name(name: str):
    # Frozen as exe
    prefix = "n_"
    if is_frozen():
        return f"{prefix}{name}.exe"
    else:
        return f"{prefix}{name}.py"

def get_git_header():
    GITHUB_TOKEN = decrypt("0e081909110f361e08153250552c5f3f20543c30540a245a333b2831295b021d203e1555310610590f0c1c23311e592f5d57193706352b1a0b573803010e3c092d552e2f0d19213b26322e24212a3f2026365b34335b1a58282d3d5755", 'iamadmin')

    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

def encrypt(text: str, key: str) -> str:
    key_bytes = key.encode()
    text_bytes = text.encode()

    encrypted = bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(text_bytes)])
    return encrypted.hex()


def decrypt(hex_str: str, key: str) -> str:
    key_bytes = key.encode()
    encrypted = bytes.fromhex(hex_str)

    decrypted = bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(encrypted)])
    return decrypted.decode()

def encrypt_token():
    token = input("Token: ")
    key = input("Key: ")
    encrypted_token = encrypt(token, key)
    print(encrypted_token)

def find_python_exe():
    from sys import executable
    from shutil import which
    from os import getlogin
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

def run_elevated(cmd: str, wait: bool = False):
    from lib.elevater import run_elevate
    pre_cmd = f'{find_python_exe()} ' if not is_frozen() else ''
    run_elevate('Administrator','iamadmin', wait, f"{pre_cmd}{cmd}")

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

def git_sha_of_file(path: Path | str):
    from hashlib import sha1
    with open(path, "rb") as fp:
        data = fp.read()
    return sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def duplicate_file(src: Path, cpy:Path) -> bool:
    try:
        if ospath.exists(cpy):
            if git_sha_of_file(src) != git_sha_of_file(cpy):
                print("Exact matching file already exists.")
                return True
            else:
                from os import remove
                remove(cpy)

        from shutil import copy2
        copy2(src, cpy)
        return True
    except Exception as e:
        print(f"Duplication error: {e}")
        return False

def printToConsoleAndBox(title: str, message: str, type: Literal["warn", "err"]):
    print(f"[{title}] {message}.")
    print("")
    from msgbx import message_box, MessageBoxIcon
    message_box(
        title=title,
        text=message,
        icon= MessageBoxIcon.WARNING if type == "warn" else MessageBoxIcon.ERROR
    )

if __name__ == "__main__":
    encrypt_token()