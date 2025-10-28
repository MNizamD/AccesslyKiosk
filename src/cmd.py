import json
import sys
import variables as v
import lock_down_utils as ldu

ARGS = sys.argv
func_map_files = {
    'cache': v.CACHE_FILE,
    'detail': v.DETAILS_FILE,
    'details': v.DETAILS_FILE
}

def get_input(msg: str = ">> "):
    return input(msg)

import json

def set(line: list):
    if len(line) != 3:
        print("Argument incomplete, usage: <function> <key> <value>")
        return

    func, key, value = line

    # ✅ Validate function name
    if func not in func_map_files:
        print(f"Unknown function '{func}'. Valid options: {', '.join(func_map_files.keys())}")
        return

    # ✅ Try to parse JSON type safely
    try:
        value = json.loads(value)
    except json.JSONDecodeError:
        value = value  # keep as string if not JSON

    # ✅ Read data
    data = ldu.read_json_cache(func_map_files[func])

    if key not in data:
        print(f"Unknown key '{key}'. Valid keys: {', '.join(data.keys())}")
        return

    # ✅ Type check
    expected_type = type(data[key])
    if not isinstance(value, expected_type):
        print(
            f"Type mismatch for key '{key}': expected {expected_type.__name__}, "
            f"got {type(value).__name__}"
        )
        return

    # ✅ Write updated value
    data[key] = value
    ldu.write_json_cache(func_map_files[func], data)
    print(f"[SUCCESS] {func}.{key} => {value} ({type(value).__name__})")

if __name__ == "__main__":
    while True:
        line = list(get_input().split())
        cmd = line[0].lower()
        if cmd == 'exit':
            break
        if cmd == 'set':
            set(line[1:])