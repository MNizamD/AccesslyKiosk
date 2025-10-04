import os
import sys
import json
import zipfile
import requests
import subprocess
import psutil
import time
import shutil
import tkinter as tk
from tkinter import ttk
from lock_down_utils import is_process_running, kill_processes, get_process_arg, run_if_not_running, check_admin

# ---------------- CONFIG ----------------
REPO_RAW = "https://raw.githubusercontent.com/MNizamD/LockDownKiosk/main"
RELEASE_URL = "https://github.com/MNizamD/LockDownKiosk/raw/main/releases/latest/download"
ZIP_BASENAME = "NizamLab"
LOCALDATA = os.getenv("LOCALAPPDATA")

def get_app_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

ARGS_DIR = get_process_arg(sys)
APP_DIR = ARGS_DIR if ARGS_DIR is not None else get_app_base_dir() 
DATA_DIR = os.path.join(LOCALDATA, "NizamLab")
FLAG_IDLE_FILE = os.path.join(DATA_DIR, "IDLE.flag")
DETAILS_FILE = os.path.join(APP_DIR, "details.json")

LOCKDOWN_FILE_NAME = "LockDown.exe"
LOCKDOWN_SCRIPT = os.path.join(APP_DIR, LOCKDOWN_FILE_NAME)
MAIN_FILE_NAME = "Main.exe"

CHECK_INTERVAL = 30  # seconds
LAST_DIR = os.path.abspath(os.path.join(APP_DIR, '..'))
TEMP_DIR = os.path.join(LAST_DIR, "tmp_update")

# ----------------------------------------

# ================= Tkinter UI =================
class UpdateWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Updater")
        self.root.geometry("400x150")
        self.root.resizable(False, False)

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


# ================= Utility ====================
def get_local_version():
    path = os.path.join(APP_DIR, DETAILS_FILE)
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)

def get_remote_version():
    url = f"{REPO_RAW}/details.json"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()

def is_main_idle():
    if is_process_running(MAIN_FILE_NAME):
        return not os.path.exists(FLAG_IDLE_FILE)
    return True

def is_lockdown_running():
    return is_process_running(LOCKDOWN_FILE_NAME)
# ==============================================


# ================= Download + Extract ==========
def download_with_progress(url, zip_path, ui: UpdateWindow):
    ui.set_message("Downloading update...")
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

def extract_zip(zip_path, temp_dir, ui: UpdateWindow):
    ui.set_message("Extracting update...")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        total = len(zf.infolist())
        for i, member in enumerate(zf.infolist(), 1):
            zf.extract(member, temp_dir)
            ui.set_progress(i / total * 100)
    os.remove(zip_path)
    ui.set_message("Extraction complete")

def replace_old_with_temp(app_dir, temp_dir, ui: UpdateWindow):
    ui.set_message("Applying update...")

    backup_dir = app_dir + "_old"
    if os.path.exists(backup_dir):
        print("Removing old backup...")
        shutil.rmtree(backup_dir)
    if os.path.exists(app_dir):
        print("Creating backup folder...")
        os.rename(app_dir, backup_dir)

    print("Replacing folder...")
    os.rename(temp_dir, app_dir)
    shutil.rmtree(backup_dir) #, ignore_errors=True)

    ui.set_message("Update applied")

def call_for_update(local_ver:str, remote_ver:str):
    try:
        print("Update available")
        ui = UpdateWindow()
        ui.set_message(f"Updating {local_ver} → {remote_ver}")

        zip_url = f"{RELEASE_URL}/{ZIP_BASENAME}-{remote_ver}.zip"
        zip_path = os.path.join(LAST_DIR, "update.zip")

        download_with_progress(zip_url, zip_path, ui)

        while not is_main_idle():
            print("Main is in used, unsafe to update")
            time.sleep(CHECK_INTERVAL)

        kill_processes([LOCKDOWN_FILE_NAME, MAIN_FILE_NAME])
        extract_zip(zip_path, TEMP_DIR, ui)
        replace_old_with_temp(APP_DIR, TEMP_DIR, ui)

        ui.set_progress(100)
        ui.set_message("Restarting LockDown...")
        time.sleep(2)
        ui.close()
        run_if_not_running(LOCKDOWN_SCRIPT, is_background=True)
        sys.exit(0)
    except Exception as e:
        print(f"[call_for_update ERR]: {e}")

    print("Update failed, retrying...")
# ==============================================


# ================= Main Loop ==================
def updater_loop():
    while True:
        if not is_lockdown_running():
            print(f"{LOCKDOWN_FILE_NAME} not running → shutting down updater.")
            sys.exit(0)

        if not is_main_idle():
            print("Main is in used, unsafe to update")
            time.sleep(CHECK_INTERVAL)
            continue

        print("Main is idle, safe to update")
        try:
            local = get_local_version()
            remote = get_remote_version()
            if not local:
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
                print("[=] Already up to date.")

        except Exception as e:
            print(f"[ERR] {e}")
            
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    check_admin("Updater")
    updater_loop()
