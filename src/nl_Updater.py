from os import path as ospath
from sys import argv, exit
import tkinter as tk
from tkinter import ttk
from lib_util import get_details_json, run_elevated, is_process_running, check_admin, kill_processes, download
from lib_env import get_env, normalize_path, ONLY_USER, PROJECT_NAME, SCHTASK_NAME, ACCESSLY_FILE_NAME, MAIN_FILE_NAME

def parse_args(args = argv[1:]):
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
                exit(1)   
            
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
REPO_RAW = "https://raw.githubusercontent.com/MNizamD/AccesslyKiosk/main"
RELEASE_URL = "https://github.com/MNizamD/AccesslyKiosk/raw/main/releases/latest/download"
ZIP_PATH = ospath.join(BASE_DIR, "update.zip")
if not env.is_dir_safe(ZIP_PATH) or (not env.is_dir_safe(BASE_DIR)):
    print("[ERROR]: Unsafe to extract zip at:", BASE_DIR)
    exit(1)
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


def get_remote_version():
    from requests import get
    try:
        url = f"{REPO_RAW}/src/details.json"
        r = get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("[GET_REMOTE_VER_ERR]:", e)
        return { "version": "? remote" }

def is_main_idle():
    if is_process_running(MAIN_FILE_NAME):
        return ospath.exists(FLAG_IDLE_FILE)
    return True
# ==============================================


# ================= Download + Extract ==========

def call_for_update(local_ver:str, remote_ver:str):
    from time import sleep
    try:
        if UPDATE_URL != None:
            print("Direct URL Update")
            remote_ver = list(UPDATE_URL.split("/")).pop()
        else:
            print("Update available")
            print(f"Updating {local_ver} → {remote_ver}")
            zip_url = f"{RELEASE_URL}/{PROJECT_NAME}-{remote_ver}.zip"
            print(zip_url)
            

        ui = UpdateWindow()
        ui.set_message(f"Downloading {remote_ver}...")
        while not download(
            src=zip_url,
            dst=ZIP_PATH,
            progress_callback=ui.set_progress
        ):
            sleep(CHECK_INTERVAL)
        ui.set_message("Download complete.")

        while not is_main_idle():
            print("Main is in used, unsafe to update")
            sleep(CHECK_INTERVAL)

        kill_processes([ACCESSLY_FILE_NAME, MAIN_FILE_NAME])
        # Step 1: Extract the zip file
        from zipper import extract_zip_dynamic, cleanup_extracted_files
        ui.set_message("Extracting update...")
        item_paths = extract_zip_dynamic(
            zip_path=ZIP_PATH,
            extract_to=BASE_DIR,
            del_zip_later=True,          # True if you want to delete the .zip after extraction
            progress_callback=ui.set_progress
        )
        # ui.set_message("Extraction complete")

        # Step 2: Clean up old/unexpected files in that folder
        ui.set_message("Cleaning up...")
        cleanup_extracted_files(
            extract_to=BASE_DIR,
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
        # run_if_not_running([f'schtasks /run /tn "{v.SCHTASK_NAME}"'], is_background=True)
        run_elevated(f'schtasks /run /tn "{SCHTASK_NAME}"')
        # run_if_not_running([ACCESSLY_SCRIPT], is_background=True)
        # run_elevate(USER,'',False, ACCESSLY_SCRIPT)
        exit(0)
    except Exception as e:
        print(f"[call_for_update ERR]: {e}")

    print("Update failed, retrying...")
# ==============================================


# ================= Main Loop ==================
def updater_loop():
    from time import sleep
    while True:
        if FORCE_RUN:
            print("FORCE RUN")
        if not FORCE_RUN and not is_process_running(ACCESSLY_FILE_NAME):
            print(f"{ACCESSLY_FILE_NAME} not running → shutting down updater.")
            exit(0)

        if not is_main_idle():
            print("Main is in used, unsafe to update")
            sleep(CHECK_INTERVAL)
            continue

        print("Main is idle, safe to update")
        try:
            local = get_details_json(DETAILS_FILE)
            remote = get_remote_version()
            if not local or not remote:
                call_for_update("corrupted", remote_ver)
                sleep(CHECK_INTERVAL)
                continue

            local_ver = local["version"]
            remote_ver = remote["version"]

            if local_ver != remote_ver:
                call_for_update("corrupted", remote_ver)
                sleep(CHECK_INTERVAL)
                continue
                
            else:
                print(f"[=] Version {local_ver} is already up to date.")

        except Exception as e:
            print(f"[ERR] {e}")
            
        sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    check_admin("Updater")
    if not env.is_dir_safe(DATA["dir"]):
        exit(0)
    updater_loop()
