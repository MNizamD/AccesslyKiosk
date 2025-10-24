import sys
import ctypes
from ctypes import wintypes

LOGON_WITH_PROFILE = 0x00000001
CREATE_NEW_CONSOLE = 0x00000010

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


CreateProcessWithLogonW = ctypes.windll.advapi32.CreateProcessWithLogonW
CreateProcessWithLogonW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
    wintypes.DWORD,
    wintypes.LPCWSTR,
    wintypes.LPWSTR,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.LPCWSTR,
    ctypes.POINTER(STARTUPINFO),
    ctypes.POINTER(PROCESS_INFORMATION),
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

INFINITE = 0xFFFFFFFF


def get_process_arg():
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:])
    return None


def run_elevate(arg_command: str):
    user = "Administrator"
    domain = "."
    password = "iamadmin"
    arguements = arg_command.split("--")
    command = arguements.pop(0)
    willWait = "wait" in list(arg.lower() for arg in arguements)

    print(f"[DEBUG] Running as {domain}\\{user}: {command}")

    si = STARTUPINFO()
    si.cb = ctypes.sizeof(STARTUPINFO)
    pi = PROCESS_INFORMATION()

    cmd_buf = ctypes.create_unicode_buffer(command)

    success = CreateProcessWithLogonW(
        user,
        domain,
        password,
        LOGON_WITH_PROFILE,
        None,
        cmd_buf,
        CREATE_NEW_CONSOLE,
        None,
        None,
        ctypes.byref(si),
        ctypes.byref(pi),
    )

    if not success:
        raise ctypes.WinError()
    
    if willWait:
        print(f"[INFO] Process started (PID={pi.dwProcessId}). Waiting for it to finish...")

        WaitForSingleObject(pi.hProcess, INFINITE)
        exit_code = wintypes.DWORD()
        GetExitCodeProcess(pi.hProcess, ctypes.byref(exit_code))
        print(f"[INFO] Process exited with code {exit_code.value}")

        CloseHandle(pi.hThread)
        CloseHandle(pi.hProcess)
    
    else:
        print(f"Started, PID: {pi.dwProcessId}")


if __name__ == "__main__":
    arg_command = get_process_arg()
    if not arg_command:
        print("Usage: elevate.py \"cmd /k echo hello & pause\"")
        sys.exit(1)

    run_elevate(arg_command)
