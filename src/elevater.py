import sys
import ctypes
from ctypes import wintypes
import subprocess

LOGON_WITH_PROFILE = 0x00000001
CREATE_NEW_CONSOLE = 0x00000010
INFINITE = 0xFFFFFFFF

class STARTUPINFO(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("lpReserved", wintypes.LPWSTR),
        ("lpDesktop", wintypes.LPWSTR),
        ("lpTitle", wintypes.LPWSTR),
        ("dwX", wintypes.DWORD),
        ("dwY", wintypes.DWORD),
        ("dwXSize", wintypes.DWORD),
        ("dwYSize", wintypes.DWORD),
        ("dwXCountChars", wintypes.DWORD),
        ("dwYCountChars", wintypes.DWORD),
        ("dwFillAttribute", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("wShowWindow", ctypes.c_short),
        ("cbReserved2", ctypes.c_short),
        ("lpReserved2", ctypes.POINTER(ctypes.c_byte)),
        ("hStdInput", wintypes.HANDLE),
        ("hStdOutput", wintypes.HANDLE),
        ("hStdError", wintypes.HANDLE),
    ]

class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("hProcess", wintypes.HANDLE),
        ("hThread", wintypes.HANDLE),
        ("dwProcessId", wintypes.DWORD),
        ("dwThreadId", wintypes.DWORD),
    ]

# Windows API setup
CreateProcessWithLogonW = ctypes.windll.advapi32.CreateProcessWithLogonW
CreateProcessWithLogonW.argtypes = [
    wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
    wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD,
    wintypes.LPVOID, wintypes.LPCWSTR,
    ctypes.POINTER(STARTUPINFO), ctypes.POINTER(PROCESS_INFORMATION)
]
CreateProcessWithLogonW.restype = wintypes.BOOL

WaitForSingleObject = ctypes.windll.kernel32.WaitForSingleObject
WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
WaitForSingleObject.restype = wintypes.DWORD

GetExitCodeProcess = ctypes.windll.kernel32.GetExitCodeProcess
GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
GetExitCodeProcess.restype = wintypes.BOOL

CloseHandle = ctypes.windll.kernel32.CloseHandle
CloseHandle.argtypes = [wintypes.HANDLE]
CloseHandle.restype = wintypes.BOOL


def user_exists(username: str) -> bool:
    """Check if a local Windows user exists."""
    try:
        result = subprocess.run(
            ["net", "user", username],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True
        )
        return result.returncode == 0
    except Exception:
        return False


def parse_args():
    args = sys.argv[1:]
    user = "Administrator"
    password = "iamadmin"
    will_wait = False
    command_parts = []

    i = 0
    while i < len(args):
        arg = args[i].lower()
        if arg == "--user":
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                user = args[i + 1]
                i += 1
            else:
                print("[ERROR] Missing value for --user")
                sys.exit(1)
        elif arg == "--password":
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                password = args[i + 1]
                i += 1
            else:
                password = ""
                # print("[ERROR] Missing value for --password")
                # sys.exit(1)

        elif arg == "--wait":
            will_wait = True
        else:
            command_parts.append(args[i])
        i += 1

    command = " ".join(command_parts).strip()
    if not command:
        print("Usage: elevate.py [--user <user>] [--password <pass>] [--wait] \"<command>\"")
        sys.exit(1)

    return user, password, will_wait, command


def run_elevate(user: str, password: str, will_wait: bool, command: str):
    domain = "."

    # Check if user exists
    if not user_exists(user):
        print(f"[ERROR] User '{user}' does not exist.")
        sys.exit(1)

    # Print info
    pw_display = "(blank)" if password == "" else ("*" * len(password))
    print(f"[DEBUG] Running as {domain}\\{user} with password {pw_display}: {command}")

    si = STARTUPINFO()
    si.cb = ctypes.sizeof(STARTUPINFO)
    pi = PROCESS_INFORMATION()
    cmd_buf = ctypes.create_unicode_buffer(command)

    success = CreateProcessWithLogonW(
        user, domain, password,
        LOGON_WITH_PROFILE,
        None, cmd_buf,
        CREATE_NEW_CONSOLE,
        None, None,
        ctypes.byref(si),
        ctypes.byref(pi)
    )

    if not success:
        err = ctypes.GetLastError()
        # if err == 1327:
        #     print("[ERROR] Blank passwords are not allowed for network logons. "
        #           "Enable them in Local Security Policy or set a password.")
        # raise ctypes.WinError(err)
        print(ctypes.WinError(err), f"\n [COMMAND] {command}")
        sys.exit(0)

    if will_wait:
        print(f"[INFO] Process started (PID={pi.dwProcessId}). Waiting...")
        WaitForSingleObject(pi.hProcess, INFINITE)
        exit_code = wintypes.DWORD()
        GetExitCodeProcess(pi.hProcess, ctypes.byref(exit_code))
        print(f"[INFO] Process exited with code {exit_code.value}")
    else:
        print(f"[INFO] Started, PID={pi.dwProcessId}")

    # Cleanup handles
    CloseHandle(pi.hThread)
    CloseHandle(pi.hProcess)


if __name__ == "__main__":
    user, password, will_wait, command = parse_args()
    run_elevate(user, password, will_wait, command)
