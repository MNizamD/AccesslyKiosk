import __fix1__
import sys
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
from mylib.util import (
    destruct,
    duplicate_file,
    run_elevated,
    printToConsoleAndBox,
    get_cur_dir,
)


def import_external(module_path: Path):
    sys.path.insert(0, str(module_path.parent))  # <── add containing folder
    spec = spec_from_file_location(str(module_path.name), str(module_path))
    if spec is None or spec.loader is None:
        raise FileNotFoundError(f"{module_path} not found.")
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------- services ----------------
def run_services(force: bool = False):
    from mylib.env import get_env

    env = get_env(get_cur_dir())
    force_arg = "--force" * int(force)
    services_path = env.services_path()
    services_path_temp = env.services_path(temp=True)
    if duplicate_file(services_path, services_path_temp):
        run_elevated(
            cmd=f'{services_path_temp} --dir {env.app_dir()} --user "{env.user()}" {force_arg}'
        )
    else:
        raise Exception("Failed to duplicate updater.")


def check_server() -> bool:
    from mylib.conn import fetch_database, find_dict, internet_ok

    if not internet_ok():
        print("No internet.")
        return True

    result = fetch_database(
        select_=["key", "value"], from_="app_status", where_="deleted_at is NULL"
    )
    if result is None:
        raise Exception("Could not reach server.")

    data = find_dict(data=result, column="key", value="is_enabled")
    if data is None or "value" not in data or not isinstance(data["value"], bool):
        raise Exception("Invalid data from server.")

    if not data["value"]:
        print("Disabled on server.")
        destruct(0)

    return True


def run_web_wall():
    run_services()
    APP_DIR = (
        Path(sys.executable).parent
        if getattr(sys, "frozen", False)
        else Path(sys.argv[0]).parent
    )
    app = import_external(APP_DIR / "web_wall" / "app.py")
    app.run(str(APP_DIR / "web_wall"))


def run():
    check_server()
    run_web_wall()


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        printToConsoleAndBox(title="Launcher Error", message=str(e), type="err")
