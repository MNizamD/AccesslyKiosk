import __fix__
import sys
from os import path as ospath
from time import sleep
from typing import Any, Literal, Optional
from lib.util import is_process_running, check_admin
from lib.env import get_env, normalize_path, ONLY_USER, SCHTASK_NAME

def destruct(exitcode:int):
    sleep(exitcode * 10) # if exit==1 -> sleep in 1*10 secs
    sys.exit(exitcode)

ParseArgsType = dict[Literal["dir","user","update","force"], Any]
def parse_args(args = sys.argv[1:]) -> ParseArgsType:
    data:ParseArgsType = {
        'dir': None,
        'update': None,
        'user': ONLY_USER,
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

# ================ Update Logic ================
class UpdateSystem:
    CHECK_INTERVAL = 15
    def __init__(self, args:ParseArgsType):
        self.env = get_env(sys=sys, user=args["user"])
        self.BASE_DIR = normalize_path(args["dir"]) if args["dir"] != None else self.env.base_dir
        self.ZIP_PATH = ospath.join(self.BASE_DIR, "update.zip")
        if not self.env.is_dir_safe(self.ZIP_PATH) or (not self.env.is_dir_safe(self.BASE_DIR)):
            raise Exception("[ERROR]: Unsafe to extract zip at:", self.BASE_DIR)
        
        self.FORCE_RUN = args["force"]
        self.APP_DIR = ospath.join(self.BASE_DIR, 'src')
        self.UPDATE_URL = args["update"]
        self.FLAG_IDLE_FILE = self.env.flag_idle_file
        self.DETAILS_FILE = ospath.join(self.APP_DIR, "details.json")
        self.ACCESSLY_SCRIPT = ospath.join(self.APP_DIR, self.env.app_file_name("accessly"))
        self.GIT_OWNER = "MNizamD"
        self.GIT_REPO = "AccesslyKiosk"
        self.GIT_D_PATH = "releases/latest/download"

    # ================= Main Loop ==================
    def run_loop(self):
        if self.FORCE_RUN:
            print("Force running...")

        from lib.conn import internet_ok
        while True:
            if not self.FORCE_RUN and not is_process_running(self.env.app_file_name("accessly")):
                print(f"{self.env.app_file_name("accessly")} not running → shutting down updater.")
                destruct(0)

            if not internet_ok():
                print("No internet connection.")
                sleep(self.CHECK_INTERVAL)
                continue

            if not self.is_main_idle():
                print("Main is in used, unsafe to update.")
                sleep(self.CHECK_INTERVAL)
                continue

            print("Safe to update.")
            self.initiate_update()
            sleep(self.CHECK_INTERVAL)

    def get_remote_version(self) -> dict[str, Optional[str]]:
        from requests import get
        try:
            REPO_RAW = f"https://raw.githubusercontent.com/{self.GIT_OWNER}/{self.GIT_REPO}/main"
            url = f"{REPO_RAW}/src/details.json"
            r = get(url, timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print("[GET_REMOTE_VER_ERR]:", e)
            return { "version": None }
        
    def get_latest_release_asset(self) -> dict[Literal['name','url','version'], str] | None:
        """
        Returns a list of dicts with 'name' and 'download_url' for all files
        in the GitHub repo folder releases/latest/download.
        """
        from requests import get
        url = f"https://api.github.com/repos/{self.GIT_OWNER}/{self.GIT_REPO}/contents/{self.GIT_D_PATH}"

        r = get(url)
        if r.status_code == 404:
            raise FileNotFoundError(f"Path '{self.GIT_D_PATH}' not found in repo {self.GIT_OWNER}/{self.GIT_REPO}")
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
    
    def call_for_update(
            self,
            local_ver:Optional[str],
            remote_ver:Optional[str],
            url: str,
            filename: str,
            reason: Literal["outdated", "invalid"]
        ):
        from lib.env import is_frozen
        import sys
        if not is_frozen(sys):
            print(f"Update available but app is not frozen.")
        if reason == "outdated":
            print(f"Update Available! {local_ver} -> {remote_ver}")
        elif reason == "invalid":
            print("Invalid Versions. Update Required!")
        try:            
            from ui.ui_updater import UpdateWindow
            ui = UpdateWindow()
            ui.set_message(f"Downloading {filename}...")
            from lib.conn import download
            while not download(
                src=url,
                dst=self.ZIP_PATH,
                progress_callback=ui.set_progress
            ):
                sleep(self.CHECK_INTERVAL)
            else:
                ui.set_message("Download complete.")

            while not self.is_main_idle():
                print("Main is in used, unsafe to execute extract")
                sleep(self.CHECK_INTERVAL)
            
            from lib.util import kill_processes
            kill_processes(self.env.all_app_processes())
            # Step 1: Extract the zip file
            from lib.zipper import extract_zip_dynamic, cleanup_extracted_files
            ui.set_message(f"Updating {local_ver} -> {remote_ver}")
            item_paths = extract_zip_dynamic(
                zip_path=self.ZIP_PATH,
                extract_to=str(self.BASE_DIR),
                del_zip_later=True,          # True if you want to delete the .zip after extraction
                progress_callback=ui.set_progress
            )

            # Step 2: Clean up old/unexpected files in that folder
            ui.set_message("Cleaning up...")
            cleanup_extracted_files(
                extract_to=str(self.BASE_DIR),
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
            from lib.util import run_elevated
            run_elevated(f'schtasks /run /tn "{SCHTASK_NAME}"')
            destruct(0)
        except Exception as e:
            print(f"[call_for_update ERR]: {e}")
        
        finally:
            sleep(self.CHECK_INTERVAL)


    def is_main_idle(self):
        if is_process_running(self.env.app_file_name("main")):
            return ospath.exists(self.FLAG_IDLE_FILE)
        return True
    
    def initiate_update(self):
        from lib.util import get_details_json
        local = get_details_json(env=self.env)
        local_ver = local["version"]

        remote_ver = None
        filename = None
        url = None

        def get_asset() -> dict[Literal['name','url','version'], str] | None:
            if self.UPDATE_URL:
                name = get_download_filename(self.UPDATE_URL, "update.zip")
                return {
                    "name": name,
                    "url": self.UPDATE_URL,
                    "version": extract_version(name)
                }
            return self.get_latest_release_asset()


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
            self.call_for_update(
                local_ver=local_ver,
                remote_ver= remote_ver,
                url=url,
                filename=filename,
                reason="outdated" if outdated_version else "invalid"
            )
        else:
            print(f"[=] Version {local_ver} is already up to date.")

# ================= Download + Extract ==========

def extract_version(filename: str) -> str:
    from re import search
    match = search(r"-([0-9]+(?:\.[0-9]+){1,})\.zip$", filename)
    return match.group(1) if match else 'unknown_ver'

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


if __name__ == "__main__":
    # print(util)
    # destruct(0)
    try:
        check_admin("Updater")
        updater = UpdateSystem(parse_args())
        updater.run_loop()
    except Exception as e:
        from lib.util import showToFronBackEnd
        showToFronBackEnd(
            title="Updater Error",
            msg=str(e),
        )
        destruct(1)