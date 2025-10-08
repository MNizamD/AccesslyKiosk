import wexpect
import time
import sys

def get_process_arg(system):
    if len(system.argv) > 1:
        return system.argv[1]
    return None

ARGS_FILE = get_process_arg(sys)
EXE_FILE = ARGS_FILE if ARGS_FILE is not None else ''

if __name__ == "__main__":
    user = "Administrator"
    command = f'runas /user:{user} {EXE_FILE}'
    print("Commad:", command)
    child = wexpect.spawn(command)

    child.expect(f'password for {user}: ')   # exact prompt text may vary
    time.sleep(1)
    child.sendline('iamadmin')
    child.sendline('exit')
    child.terminate()
    print(child.before)