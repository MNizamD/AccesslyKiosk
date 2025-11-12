import __fix__
import sys
from typing import Any, Iterable, Optional
from lib.env import get_env, ONLY_USER

ARGS = sys.argv[1:]
env = get_env(sys=sys)

def FUNC_MAP_FILES():
    return {
        'cache': env.cache_file,
        'detail': env.details_file,
    }

def parse_args(args: 'list[str]', args_names: 'list[str]') -> tuple[dict[str, Any], list[str]]:
    data: dict[str, Any] = {}
    for k in args_names:
        data[k] = None
    command_parts: list[str] = []
    i = 0

    # valid_args = ['--user']
    valid_args = list(f'--{a}' for a in args_names)
    while i < len(args):
        arg = args[i].lower()
        if arg in valid_args:
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                data[arg[2:]] = args[i + 1]
                i += 1
            else:
                print(f"[ERROR] Missing value for --{arg}")
                exit(1)   
        else:
            command_parts.append(args[i])
        i += 1
    return data, command_parts

def parse_typed_value(raw: str) -> str | Any:
    """
    Parses a string like 'int//5' or 'str//hello' and casts the value to the given type.
    """
    if "//" not in raw:
        return raw  # return as-is if no type indicator

    type_name, value_str = raw.split("//", 1)
    type_name = type_name.strip().lower()
    value_str = value_str.strip()

    # Mapping of supported types
    type_map = {
        "int": int,
        "float": float,
        "str": str,
        "bool": lambda v: v.lower() in ("1", "true", "yes", "on"),
    }

    if type_name not in type_map:
        print(f"[WARN] Unknown type '{type_name}', returning as string.")
        return raw

    try:
        return type_map[type_name](value_str)
    except Exception as e:
        print(f"[ERROR] Failed to cast '{value_str}' as {type_name}: {e}")
        return raw


def get_input(msg: str = "", pref: str = ">>"):
    return input(f'{pref}{msg} ')

def invalid_option(type: str, func: str, options: Iterable) -> str:
    return f"Unknown {type} '{func}'. Valid options: " + "".join(f"\n--> {op}" for op in options)

def n_set(line: list):
    from json import loads, JSONDecodeError
    if len(line) != 3:
        print("Argument incomplete, usage: <function> <key> <value>")
        return

    func, key, value = line
    force_cast = "//" in value
    value = parse_typed_value(value)
    if not force_cast:
        try:
            value = loads(value)
        except JSONDecodeError:
            value = value  # keep as string if not JSON    
    
    data = n_get([func], False)
    if data is None:
        return
    
    # ✅ Type check
    expected_type = type(data[key])
    if not force_cast and not isinstance(value, expected_type):
        print(
            f"Type mismatch for key '{key}': expected {expected_type.__name__}, "
            f"got {type(value).__name__}"
        )
        return
    
    # ✅ Write updated value
    data[key] = value
    from lib.util import write_json
    write_json(str(FUNC_MAP_FILES()[func]), data)
    print(f"[SUCCESS] {func}.{key} => {value} ({type(value).__name__})")

def n_get(line: list, read: bool=True):
    if len(line) < 1:
        raise ValueError(f"Argument incomplete, usage: <{'/'.join(FUNC_MAP_FILES().keys())}> <dir?/key?>")
    if len(line) > 2:
        raise ValueError(f"Argument overflow, usage: <{'/'.join(FUNC_MAP_FILES().keys())}> <dir?/key?>")
    func = line[0]
    key = line[1] if len(line) > 1 else None
    data = get_json(func)
    if data is None:
        return None
    if key is None:
        if read: print(f"{str(func).upper()}: {data}")
        return data
    elif key == 'dir':
        print(f"{func}: {FUNC_MAP_FILES()[func]}")
        return None
    
    if key not in data or data[key] is None:
        print(invalid_option("key", key, data.keys()))
        return None
    else:
        if read:
            print(f"{str(key).upper()}: {data[key]}")
        return data[key]
        

def get_json(func: str) -> Optional['dict[str, Any]']:
    # ✅ Validate function name
    if func not in FUNC_MAP_FILES():
        raise ValueError(invalid_option('function', func, FUNC_MAP_FILES().keys()))
    # ✅ Read data
    from lib.util import read_json
    return read_json(str(FUNC_MAP_FILES()[func]))

def n_update(_):
    from os import path as ospath
    from lib.util import kill_processes, run_elevated, duplicate_file
    # path = "%ProgramData%\\MyApp\\config.json"
    url = input("DOWNLOAD LINK (Optional): ").strip()
    path = input("APP PATH (Optional): ").strip()
    user = input("ACC USER (GVC): ").strip()
    BASE_DIR = ospath.expandvars(path if len(path) else env.base_dir)
    USER = f'--user {user}' if len(user) else ONLY_USER
    D_URL = f'--update {url}' if len(url) else ''
    # "--dir C:\Users\Marohom\Documents\NizamLab\playground --user GVC --force --update 
    # https://github.com/MNizamD/AccesslyKiosk/raw/main/releases/old_versions/NizamLab-0.4.7.zip
    kill_processes(env.all_app_processes())
    duplicate_file(env.script_updater, env.script_updater) 
    run_elevated(f'{env.script_updater_copy} --dir {BASE_DIR} {USER} {D_URL} --force')

def n_task_manager(line: 'list[str]'):
    from lib.util import is_process_running, kill_processes
    if len(line) < 2:
        print("Argument incomplete, usage: <check/kill> <app/task_names>")
        return None
    mode = line[0].lower()
    tasks = line[1:]

    if 'app' in tasks:
        tasks.remove('app')
        tasks += env.all_app_processes()

    if mode == 'check':
        for task in tasks:
            result = is_process_running(task)
            if result.running:
                print(f"[{result.data["pid"]}] {task}: {result.data["exe"]}")
            else:
                print(f"{task} is inactive")
    elif mode == 'kill':
        kill_processes(tasks, False)
    else:
        print("Invalid function, usage: <check/kill> <task_names>")

def n_info(_):
    from lib.env import get_cur_user, get_run_dir
    data = n_get(line=['detail'], read=False)
    if data is None:
        print("Cannot get info.")
    
    print(f"\n======= CLI =======")
    print(f"User: {get_cur_user()}")
    print(f"Directory: {get_run_dir(sys=sys)}")
    print(f"\n======= APP =======")
    print(f'User: {env.user}')
    print(f'Version: {data['version'] if data != None else 'Unknown'}')
    print(f'Version: {data['version'] if data != None else 'Unknown'}')
    print(f'Updated: {data['updated'] if data != None else 'Unknown'}')
    print(f'Directory: {env.base_dir}')
    print(f"Data: {env.data_dir}")
    print(f"Cache: {env.cache_dir}")
    print(f"Temp: {env.temp}")
    n_task_manager(['check', 'app'])

commands = {
    'set': {
        'method': n_set     # ← same here
    },
    'get': {
        'method': n_get
    },
    'help': {
        'method': lambda args: print(f"Valid options: \n>  {'\n>  '.join(commands.keys())}")  # lambda for inline behavior
    },
    'task': {
        'method': n_task_manager
    },
    'info': {
        'method': n_info
    },
    'update': {
        'method': n_update
    },
    'exit': {
        'method': lambda _: sys.exit(0)  # ← store function reference, don't call it yet
    }
}

if __name__ == "__main__":
    data = parse_args(ARGS, ['user'])
    user = data[0]['user']
    command_parts = data[1]
    if user != None:
        env.set_user(user)

    while True:
        if len(command_parts):
            line = command_parts.copy()
            command_parts.clear()
        else:
            line = get_input().split()
        if not line:
            continue
        cmd = line.pop(0).lower()
        args = line
        if cmd not in commands:
            print(f"Unknown command {cmd}. Valid options: \n>  {'\n>  '.join(commands.keys())}")
            continue

        try:
            commands[cmd]['method'](args)
        except SystemExit:
            print("Exiting...")
            break
        except Exception as e:
            print(f"[ERROR] {e}")