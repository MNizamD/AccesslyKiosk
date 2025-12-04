if __name__ == "__main__":
    import __fix2__
import sys
from typing import Any, Literal
from concurrent.futures import ThreadPoolExecutor, as_completed
from os import path as ospath, remove, walk, makedirs
from requests import get
from pathlib import Path

from mylib.util import (
    git_sha_of_file,
    ONLY_USER,
    is_user_exists,
    printToConsoleAndBox,
    destruct,
    get_git_header,
)

ParseArgsType = dict[Literal["dir", "user", "update", "force"], Any]


def parse_args(args: list) -> ParseArgsType:
    data: ParseArgsType = {
        "dir": None,
        "update": None,
        "user": ONLY_USER,
        "force": False,
    }

    i = 0
    valid_args = ["--user", "--url", "--dir", "--update"]
    while i < len(args):
        arg = args[i].lower()
        if arg in valid_args:
            if i + 1 < len(args) and not str(args[i + 1]).startswith("--"):
                data[arg[2:]] = args[i + 1]  # type: ignore
                i += 1
            else:
                raise Exception(f"[ERROR] Missing value for --{arg}")

        elif arg == "--force":
            data["force"] = True
        i += 1

    return data
    # --dir C:\Users\Marohom\Documents\NizamLab\playground --user GVC --force


class Updater:
    _instance = None  # singleton-style cache

    def __new__(cls, cmd: list[str]):
        # ✅ Lazy singleton — only one instance per project
        if cls._instance is None or cls._instance._cmd != cmd:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, cmd: list[str]):
        if self._initialized:
            return  # skip re-init if already created

        args = parse_args(cmd)
        if not is_user_exists(args["user"]):
            raise ValueError(f"User '{args["user"]}' does not exist on this computer.")

        if not args["dir"]:
            raise ValueError("No directory was passed.")
        if not Path(args["dir"]).exists():
            raise FileNotFoundError("Directory not found.")
        if "testing" in str(args["dir"]).lower():
            raise Exception(f"Directory is in testing ({args['dir']})")

        self._cmd = args
        from mylib.env import get_env

        self.env = get_env(Path(args["dir"]), args["user"])
        self.app_dir = Path(args["dir"])
        self.update_url = args["update"]
        self.forced: bool = args["force"]

        self.GIT_OWNER = "MNizamD"
        self.GIT_REPO = "AccesslyKiosk"
        self.GIT_D_PATH = "dist/web_wall"
        self.GIT_HEADER = get_git_header()

        self.max_threads = 10  # You can increase up to 32 for even faster speeds
        self._initialized = True

    def get_local_details(self) -> dict[str, str | None]:
        path = self.env.local_detail_path()
        from json import load

        try:
            if not path.exists():
                raise FileNotFoundError(f"Missing details: {path}")
            with open(path, "r", encoding="utf-8") as f:
                return load(f)

        except Exception as e:
            print("[GET_LOCAL_DETAILS_ERR]:", e)
            return {"version": None}

    def get_remote_details(self) -> dict[str, str | None]:
        try:
            REPO_RAW = f"https://raw.githubusercontent.com/{self.GIT_OWNER}/{self.GIT_REPO}/main"
            url = f"{REPO_RAW}/{self.GIT_D_PATH}/details.json"
            r = get(url, timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print("[GET_REMOTE_DETAILS_ERR]:", e)
            return {"version": None}

    def initiate_update(self):
        from mylib.conn import internet_ok

        if not internet_ok(quiet=True):
            print("[Updater]: No internet.")
            return

        local_version = self.get_local_details().get("version", None)
        remote_version = self.get_remote_details().get("version", None)
        print(local_version, "?", remote_version)
        if remote_version is None:
            raise Exception("Could not fetch remote version.")

        print(self.get_rate_limit())
        if local_version != remote_version:
            print(f"Update available: {remote_version}")
            self.sync_github_to_local()
        else:
            print("No update available.")

    def sync_github_to_local(self):
        remote_files = self.fetch_repo_tree(self.GIT_D_PATH)
        local_files = self.app_dir / "web_wall"

        normalized = []
        print("Fetching repository tree...")
        for f in remote_files:
            relative = f["path"].replace(self.GIT_D_PATH, "").lstrip("/")
            local = ospath.join(local_files, relative)
            normalized.append({"github": f, "local_path": local, "relative": relative})

        # Ensure folders exist
        for f in normalized:
            makedirs(ospath.dirname(f["local_path"]), exist_ok=True)

        # Files to download or update
        tasks = []

        for f in normalized:
            local_path = f["local_path"]
            github = f["github"]
            relative = f["relative"]

            if not ospath.exists(local_path):
                print("Queue NEW:", relative)
                tasks.append((github, local_path, relative))
                continue

            if git_sha_of_file(local_path) != github["sha"]:
                print("Queue UPDATED:", relative)
                tasks.append((github, local_path, relative))

        # 🔥 PARALLEL DOWNLOAD
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = [
                executor.submit(self.download_file, github, local_path, relative)
                for github, local_path, relative in tasks
            ]
            for _ in as_completed(futures):
                pass  # just wait for all to finish

        # Step 2 — Delete missing files
        remote_set = {f["relative"] for f in normalized}

        for root, _, files in walk(local_files):
            for file in files:
                full = ospath.join(root, file)
                relative = ospath.relpath(full, local_files).replace("\\", "/")

                if relative not in remote_set:
                    print("Deleting REMOVED file:", relative)
                    remove(full)

    def get_rate_limit(self):
        r = get("https://api.github.com/rate_limit", headers=self.GIT_HEADER)
        result = r.json().get("rate", None)
        if "reset" in result:
            from datetime import datetime

            result["reset"] = str(datetime.fromtimestamp(1763170498))
        return result

    def fetch_repo_tree(self, path) -> list:
        url = f"https://api.github.com/repos/{self.GIT_OWNER}/{self.GIT_REPO}/contents/{path}"
        r = get(url, timeout=10, headers=self.GIT_HEADER)
        r.raise_for_status()

        items = r.json()
        files = []

        for item in items:
            if item["type"] == "file":
                files.append(
                    {
                        "path": item["path"],
                        "download_url": item["download_url"],
                        "sha": item["sha"],
                    }
                )
            elif item["type"] == "dir":
                files.extend(self.fetch_repo_tree(item["path"]))

        return files

    def download_file(self, github_data, local_path, relative):
        """Downloads a single file in a separate thread."""
        try:
            content = get(github_data["download_url"]).content
            with open(local_path, "wb") as fp:
                fp.write(content)
            print("Downloaded:", relative)
        except Exception as e:
            print("Failed to download:", relative, str(e))


def run(cmd: list[str]):
    try:
        updater = Updater(cmd=cmd)
        updater.initiate_update()
    except Exception as e:
        printToConsoleAndBox(title="Update Error", message=str(e), type="err")
        destruct(1)


def test():
    try:
        # updater = Updater(sys.argv[1:])
        # # sync_github_to_local()
        # print(updater.get_rate_limit())
        # print(updater.app_dir)
        # # print(env.launcher_path())
        # # print(env.services_path())
        # # print(env.local_detail_path())
        # # print(env.app_dir())
        # print(updater.get_local_details())
        # print(updater.get_remote_details())
        # updater.initiate_update()
        run(sys.argv[1:])
    except Exception as e:
        print(e)
        destruct(1)


if __name__ == "__main__":
    test()
