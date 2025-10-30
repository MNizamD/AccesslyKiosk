from os import path as ospath
from sys import argv, exit
# import json
import requests
import time
import tkinter as tk
from tkinter import ttk
import lock_down_utils as ldu
import variables as v
from elevater import run_elevate

# ---------------- CONFIG ----------------
FORCE_RUN = len(argv)>2 and argv[2]=='--force'
BASE_DIR = argv[1] if len(argv)>1 else v.BASE_DIR
USER = argv[2] if len(argv)>2 and not FORCE_RUN else 'GVC'
FLAG_IDLE_FILE = ospath.join(rf'C:\Users\{USER}\AppData\Local\Temp', v.PROJECT_NAME,"IDLE.flag")

LOCKDOWN_FILE_NAME = v.LOCKDOWN_FILE_NAME
LOCKDOWN_SCRIPT = ospath.join(BASE_DIR,'src', LOCKDOWN_FILE_NAME)
MAIN_FILE_NAME = v.MAIN_FILE_NAME

CHECK_INTERVAL = 15  # seconds
# LAST_DIR = ldu.move_up_dir(BASE_DIR)
# TEMP_DIR = ospath.join(LAST_DIR, "tmp_update")
REPO_RAW = "https://raw.githubusercontent.com/MNizamD/LockDownKiosk/main"
RELEASE_URL = "https://github.com/MNizamD/LockDownKiosk/raw/main/releases/latest/download"
ZIP_BASENAME = v.PROJECT_NAME
ZIP_PATH = ospath.join(BASE_DIR, "update.zip")

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

    def set_progress(self, percent):
        self.progress["value"] = percent
        self.percent_label.config(text=f"{int(percent)}%")
        self.root.update()

    def close(self):
        self.root.destroy()
# ==============================================


def get_remote_version():
    try:
        url = f"{REPO_RAW}/src/details.json"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("[GET_REMOTE_VER_ERR]:", e)
        return { "version": "? remote" }

def is_main_idle():
    if ldu.is_process_running(MAIN_FILE_NAME):
        return ospath.exists(FLAG_IDLE_FILE)
    return True

def is_lockdown_running():
    return ldu.is_process_running(LOCKDOWN_FILE_NAME)
# ==============================================


# ================= Download + Extract ==========
def download_with_progress(url, zip_path, ui: UpdateWindow):
    ui.set_message("Downloading update...")
    print("Download zip at", zip_path)
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            downloaded = 0
            with open(zip_path, "wb") as f:
                for chunk in r.iter_content(8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            percent = (downloaded / total) * 100
                            ui.set_progress(percent)
        ui.set_message("Download complete")
        return True
    except Exception as e:
        print(f"[ERROR]@download_with_progress: {e}")
        return False

# def extract_zip(zip_path, temp_dir, ui: UpdateWindow):
#     ui.set_message("Extracting update...")
#     if ospath.exists(temp_dir):
#         shutil.rmtree(temp_dir)
#     makedirs(temp_dir, exist_ok=True)

#         # print(f"Progress: {pct:.2f}%")

#     with zipfile.ZipFile(zip_path, "r") as zf:
#         total = len(zf.infolist())
#         for i, member in enumerate(zf.infolist(), 1):
#             zf.extract(member, temp_dir)
#             ui.set_progress(i / total * 100)
#     rm(zip_path)
#     ui.set_message("Extraction complete")

# def replace_old_with_temp(app_dir, temp_dir, ui: UpdateWindow):
#     ui.set_message("Applying update...")

#     backup_dir = app_dir + "_old"
#     if ospath.exists(backup_dir):
#         print("Removing old backup...")
#         shutil.rmtree(backup_dir)
#     if ospath.exists(app_dir):
#         print("Creating backup folder...")
#         rn(app_dir, backup_dir)

#     print("Replacing folder...")
#     rn(temp_dir, app_dir)
#     shutil.rmtree(backup_dir) #, ignore_errors=True)

#     ui.set_message("Update applied")


def call_for_update(local_ver:str, remote_ver:str):
    try:
        print("Update available")
        ui = UpdateWindow()
        ui.set_message(f"Updating {local_ver} → {remote_ver}")
        zip_url = f"{RELEASE_URL}/{ZIP_BASENAME}-{remote_ver}.zip"

        while not download_with_progress(zip_url, ZIP_PATH, ui):
            time.sleep(CHECK_INTERVAL)

        while not is_main_idle():
            print("Main is in used, unsafe to update")
            time.sleep(CHECK_INTERVAL)

        ldu.kill_processes([LOCKDOWN_FILE_NAME, MAIN_FILE_NAME])
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
        ui.set_message("Restarting LockDown...")
        time.sleep(2)
        ui.close()
        # ldu.run_if_not_running([f'schtasks /run /tn "{v.SCHTASK_NAME}"'], is_background=True)
        ldu.run_elevated(f'schtasks /run /tn "{v.SCHTASK_NAME}"')
        # ldu.run_if_not_running([LOCKDOWN_SCRIPT], is_background=True)
        # run_elevate(USER,'',False, LOCKDOWN_SCRIPT)
        ldu.run
        exit(0)
    except Exception as e:
        print(f"[call_for_update ERR]: {e}")

    print("Update failed, retrying...")
# ==============================================


# ================= Main Loop ==================
def updater_loop():
    while True:
        if FORCE_RUN:
            print("FORCE RUN")
        if not FORCE_RUN and not is_lockdown_running():
            print(f"{LOCKDOWN_FILE_NAME} not running → shutting down updater.")
            exit(0)

        if not is_main_idle():
            print("Main is in used, unsafe to update")
            time.sleep(CHECK_INTERVAL)
            continue

        print("Main is idle, safe to update")
        try:
            local = ldu.get_details_json()
            remote = get_remote_version()
            if not local or not remote:
                call_for_update("corrupted", remote_ver)
                time.sleep(CHECK_INTERVAL)
                continue

            local_ver = local["version"]
            remote_ver = remote["version"]

            if local_ver != remote_ver:
                call_for_update("corrupted", remote_ver)
                time.sleep(CHECK_INTERVAL)
                continue
                
            else:
                print(f"[=] Version {local_ver} is already up to date.")

        except Exception as e:
            print(f"[ERR] {e}")
            
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    ldu.check_admin("Updater")
    # ldu.kill_processes(['Main.exe'])
    # print(f"{MAIN_FILE_NAME} running:", ldu.is_process_running('Main.exe'))
    # print(f"{FLAG_IDLE_FILE}:", ospath.exists(FLAG_IDLE_FILE))
    # print(is_main_idle())
    # input("C...")
    # exit(0)
    updater_loop()
