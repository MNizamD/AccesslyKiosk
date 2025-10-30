from sys import argv, exit
from variables import CACHE_FILE, DETAILS_FILE

ARGS = argv
FUNC_MAP_FILES = {
    'cache': CACHE_FILE,
    'detail': DETAILS_FILE,
    'details': DETAILS_FILE
}

def parse_typed_value(raw: str):
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
        "none": lambda v: None
    }

    if type_name not in type_map:
        print(f"[WARN] Unknown type '{type_name}', returning as string.")
        return raw

    try:
        return type_map[type_name](value_str)
    except Exception as e:
        print(f"[ERROR] Failed to cast '{value_str}' as {type_name}: {e}")
        return raw


def get_input(msg: str = ">> "):
    return input(msg)

def n_set(line: list):
    import json
    if len(line) != 3:
        print("Argument incomplete, usage: <function> <key> <value>")
        return

    func, key, value = line
    force_cast = "//" in value
    value = parse_typed_value(value)
    if not force_cast:
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            value = value  # keep as string if not JSON    
    
    if n_get([func, key], False) is None:
        return
    data = n_get([func], False)
    
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
    from lock_down_utils import write_json
    write_json(FUNC_MAP_FILES[func], data)
    print(f"[SUCCESS] {func}.{key} => {value} ({type(value).__name__})")

def n_get(line: list, read: bool=True):
    if len(line) < 1:
        print("Argument incomplete, usage: <function> <key?>")
        return
    if len(line) > 2:
        print("Argument overflow, usage: <function> <key?>")
        return
    func = line[0]
    key = line[1] if len(line) > 1 else None
    data = get_json(func)
    if data is None:
        return
    
    if key is None:
        if read: print(f"{str(func).upper()}: {data}")
        return data
    
    if key not in data:
        print(f"Unknown key '{key}'. Valid keys: \n>  {'\n>  '.join(data.keys())}")
        return None
    else:
        if read: print(f"{str(key).upper()}: {data[key]}")
        return data[key]
        

def get_json(func: str):
    # ✅ Validate function name
    if func not in FUNC_MAP_FILES:
        print(f"Unknown function '{func}'. Valid options: \n>  {'\n>  '.join(FUNC_MAP_FILES.keys())}")
        return None
    # ✅ Read data
    from lock_down_utils import read_json
    return read_json(FUNC_MAP_FILES[func])

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
    'exit': {
        'method': lambda args: exit(0)  # ← store function reference, don't call it yet
    }
}

if __name__ == "__main__":
    while True:
        line = get_input().split()
        if not line:
            continue
        cmd = line.pop(0).lower()
        args = line

        if cmd not in commands:
            print(f"Unknown command. Valid options: \n>  {'\n>  '.join(commands.keys())}")
            continue

        try:
            commands[cmd]['method'](args)
        except SystemExit:
            print("Exiting...")
            break
        except Exception as e:
            print(f"[ERROR] {e}")