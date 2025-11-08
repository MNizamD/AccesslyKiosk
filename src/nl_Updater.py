from os import path as ospath
from sys import argv, exit
from time import sleep
import tkinter as tk
from tkinter import ttk
from typing import Any, Literal, Optional, Tuple
from lib_util import get_details_json, run_elevated, is_process_running, check_admin, kill_processes, download, internet_ok, showToFronBackEnd
from lib_env import get_env, normalize_path, ONLY_USER, SCHTASK_NAME, ACCESSLY_FILE_NAME, MAIN_FILE_NAME

def destruct(exitcode:int):
    sleep(10)
    exit(exitcode)

def parse_args(args = argv[1:]) -> dict[str, Any]:
    data = {
        'dir': None,
        'user': ONLY_USER,
        'update': None,
        'force':False
        }

    i = 0
    valid_args = ['--user', '--url', '--dir', '--update']
    while i < len(args):
        arg = args[i].lower()
        if arg in valid_args:
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                data[arg[2:]] = args[i + 1]
                i += 1
            else:
                print(f"[ERROR] Missing value for --{arg}")
                destruct(1)  
            
        elif arg == "--force":
            data["force"] = True
        i += 1

    return data
    # --dir C:\Users\Marohom\Documents\NizamLab\playground --user GVC --force

    
# ---------------- CONFIG ----------------
DATA = parse_args()
FORCE_RUN = DATA["force"]
USER = DATA["user"]
env = get_env(user=USER)
BASE_DIR = normalize_path(DATA["dir"]) if DATA["dir"] != None else env.base_dir
APP_DIR = ospath.join(BASE_DIR, 'src')
UPDATE_URL = DATA["update"]
FLAG_IDLE_FILE = env.flag_idle_file
DETAILS_FILE = ospath.join(APP_DIR, "details.json")
ACCESSLY_SCRIPT = ospath.join(APP_DIR, ACCESSLY_FILE_NAME)

CHECK_INTERVAL = 15  # seconds
# REPO_RAW = "https://raw.githubusercontent.com/MNizamD/AccesslyKiosk/main"
# RELEASE_URL = "https://github.com/MNizamD/AccesslyKiosk/raw/main/releases/latest/download"
ZIP_PATH = ospath.join(BASE_DIR, "update.zip")
if not env.is_dir_safe(ZIP_PATH) or (not env.is_dir_safe(BASE_DIR)):
    print("[ERROR]: Unsafe to extract zip at:", BASE_DIR)
    destruct(1)
# ----------------------------------------

# ================= Tkinter UI =================
class UpdateWindow:
    def disable_event(self):
        print("Surpressed close")

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Updater")
        self.root.geometry("400x150")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.disable_event)

        self.label = tk.Label(self.root, text="Waiting...", font=("Arial", 12))
        self.label.pack(pady=15)

        self.progress = ttk.Progressbar(self.root, length=300, mode="determinate")
        self.progress.pack(pady=10)

        self.percent_label = tk.Label(self.root, text="0%", font=("Arial", 10))
        self.percent_label.pack(pady=5)

        self.root.update()

    def set_message(self, msg):
        self.label.config(text=msg)
        self.root.update()

    def set_progress(self, percent: float):
        self.progress["value"] = percent
        self.percent_label.config(text=f"{int(percent)}%")
        self.root.update()

    def close(self):
        self.root.destroy()
# ==============================================


def get_remote_version() -> dict[str, Optional[str]]:
    from requests import get
    try:
        REPO_RAW = "https://raw.githubusercontent.com/MNizamD/AccesslyKiosk/main"
        url = f"{REPO_RAW}/src/details.json"
        r = get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("[GET_REMOTE_VER_ERR]:", e)
        return { "version": None }

def is_main_idle():
    if is_process_running(MAIN_FILE_NAME):
        return ospath.exists(FLAG_IDLE_FILE)
    return True
# ==============================================


# ================= Download + Extract ==========

def extract_version(filename: str) -> str:
    from re import search
    match = search(r"-([0-9]+(?:\.[0-9]+){1,})\.zip$", filename)
    return match.group(1) if match else 'unknown_ver'

def get_latest_release_asset() -> dict[Literal['name','url','version'], str] | None:
    """
    Returns a list of dicts with 'name' and 'download_url' for all files
    in the GitHub repo folder releases/latest/download.
    """
    import requests

    OWNER = "MNizamD"
    REPO = "AccesslyKiosk"
    PATH = "releases/latest/download"

    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{PATH}"

    r = requests.get(url)
    if r.status_code == 404:
        raise FileNotFoundError(f"Path '{PATH}' not found in repo {OWNER}/{REPO}")
    r.raise_for_status()

    files = r.json()
    
    result: list[dict[Literal['name','url','version'], str]] = [{
        "name": str(f["name"]),
        "url": str(f["download_url"]),
        "version": extract_version(f["name"])
        } for f in files]
    result.sort(key=lambda x: x["name"], reverse=True)
    if len(result):
        return result[0]
    return None

# Example usage for AccesslyKiosk repo:
# owner = "MNizamD"
# repo = "AccesslyKiosk"
# url, fname = get_latest_release_asset(owner, repo, asset_pattern=".zip")

def get_download_filename(url: str, fallback: str) -> str:
    from requests import head
    response = head(url, allow_redirects=True)

    # 1️⃣ Try "Content-Disposition" header
    cd = response.headers.get("Content-Disposition")
    if cd and "filename=" in cd:
        filename = cd.split("filename=")[-1].strip('"\' ')
        return filename

    # 2️⃣ Try URL path
    from urllib.parse import urlparse
    path = urlparse(response.url).path
    if path:
        filename = ospath.basename(path)
        if filename:
            return filename

    # 3️⃣ Fallback generic name
    return fallback

def call_for_update(
        local_ver:Optional[str],
        remote_ver:Optional[str],
        url: str,
        filename: str,
        reason: Literal["outdated", "invalid"]
    ):
    if reason == "outdated":
        print("Update Available!")
    elif reason == "invalid":
        print("Invalid Versions. Update Required!")
    try:            

        ui = UpdateWindow()
        ui.set_message(f"Downloading {remote_ver}...")
        while not download(
            src=url,
            dst=ZIP_PATH,
            progress_callback=ui.set_progress
        ):
            sleep(CHECK_INTERVAL)
        else:
            ui.set_message("Download complete.")

        while not is_main_idle():
            print("Main is in used, unsafe to execute extract")
            sleep(CHECK_INTERVAL)

        kill_processes(env.all_app_processes())
        # Step 1: Extract the zip file
        from zipper import extract_zip_dynamic, cleanup_extracted_files
        ui.set_message("Extracting update...")
        item_paths = extract_zip_dynamic(
            zip_path=ZIP_PATH,
            extract_to=str(BASE_DIR),
            del_zip_later=True,          # True if you want to delete the .zip after extraction
            progress_callback=ui.set_progress
        )
        # ui.set_message("Extraction complete")

        # Step 2: Clean up old/unexpected files in that folder
        ui.set_message("Cleaning up...")
        cleanup_extracted_files(
            extract_to=str(BASE_DIR),
            valid_paths=item_paths,
            ignore_list=[
                "cache/",             # Whole folder to keep
                "data/",              # Another folder to ignore
                # "logs/log.txt"        # Specific file to keep
            ]
        )

        ui.set_progress(100)
        ui.set_message("Restarting Accessly...")
        sleep(2)
        ui.close()
        run_elevated(f'schtasks /run /tn "{SCHTASK_NAME}"')
        exit(0)
    except Exception as e:
        print(f"[call_for_update ERR]: {e}")
    
    finally:
        sleep(CHECK_INTERVAL)
# ==============================================

def initiate_update():
    local = get_details_json(env=env)
    local_ver = local["version"]

    remote_ver = None
    filename = None
    url = None

    def get_asset() -> dict[Literal['name','url','version'], str] | None:
        if UPDATE_URL:
            name = get_download_filename(UPDATE_URL, "update.zip")
            return {
                "name": name,
                "url": UPDATE_URL,
                "version": extract_version(name)
            }
        return get_latest_release_asset()


    latest_asset = get_asset()
    if latest_asset:
        filename = latest_asset["name"]
        url = latest_asset["url"]
        remote_ver = latest_asset["version"]

    if filename == None or url == None:
        raise FileNotFoundError("Could not find update source.")

    invalid_versions = local_ver == None or remote_ver == None
    outdated_version = local_ver != remote_ver
    if outdated_version or invalid_versions:
        call_for_update(
            local_ver=local_ver,
            remote_ver= remote_ver,
            url=url,
            filename=filename,
            reason="outdated" if outdated_version else "invalid"
        )
    else:
        print(f"[=] Version {local_ver} is already up to date.")


# ================= Main Loop ==================
def updater_loop():
    if FORCE_RUN:
        print("Force running...")

    while True:
        if not FORCE_RUN and not is_process_running(ACCESSLY_FILE_NAME):
            print(f"{ACCESSLY_FILE_NAME} not running → shutting down updater.")
            destruct(0)

        if not internet_ok():
            print("No internet connection.")
            sleep(CHECK_INTERVAL)
            continue

        if not is_main_idle():
            print("Main is in used, unsafe to update.")
            sleep(CHECK_INTERVAL)
            continue

        print("Safe to update.")
        initiate_update()
        sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        check_admin("Updater")
        if not env.is_dir_safe(DATA["dir"]):
            destruct(1)
        updater_loop()
    except Exception as e:
        showToFronBackEnd(
            title="Updater Error",
            msg=str(e),
        )
        exit(1)
    else:
        exit(0)