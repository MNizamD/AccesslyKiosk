from concurrent.futures import ThreadPoolExecutor, as_completed
from os import path as ospath, remove, walk, makedirs
from requests import get

from l_env import get_cur_dir, get_app_dir, get_local_detail_dir, get_git_header, GIT_OWNER, GIT_D_PATH, GIT_REPO

ROOT_DIR = get_cur_dir()
APP_DIR = get_app_dir()
# LOCAL_PATH = "app_folder/web_wall"

MAX_THREADS = 10  # You can increase up to 32 for even faster speeds

def get_rate_limit():
    r = get("https://api.github.com/rate_limit", headers=get_git_header())
    result = r.json().get('rate', None)
    if 'reset' in result:
        from datetime import datetime
        result["reset"] = str(datetime.fromtimestamp(1763170498))
    return result

def fetch_repo_tree(path):
    url = f"https://api.github.com/repos/{GIT_OWNER}/{GIT_REPO}/contents/{path}"
    r = get(url, timeout=10, headers=get_git_header())
    r.raise_for_status()

    items = r.json()
    files = []

    for item in items:
        if item["type"] == "file":
            files.append({
                "path": item["path"],
                "download_url": item["download_url"],
                "sha": item["sha"]
            })
        elif item["type"] == "dir":
            files.extend(fetch_repo_tree(item["path"]))

    return files


def download_file(github_data, local_path, relative):
    """Downloads a single file in a separate thread."""
    try:
        content = get(github_data["download_url"]).content
        with open(local_path, "wb") as fp:
            fp.write(content)
        print("Downloaded:", relative)
    except Exception as e:
        print("Failed to download:", relative, str(e))

def get_local_details() -> dict[str, str|None]:
    path = get_local_detail_dir()
    from json import load
    try:
        if not path.exists():
            raise FileNotFoundError(f"Missing details: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return load(f)

    except Exception as e:
        print("[GET_LOCAL_DETAILS_ERR]:", e)
        return { "version": None, "updated": None}
    
def get_remote_details() -> dict[str, str| None]:
    try:
        REPO_RAW = f"https://raw.githubusercontent.com/{GIT_OWNER}/{GIT_REPO}/main"
        url = f"{REPO_RAW}/testing/web_wall/details.json"
        r = get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("[GET_REMOTE_DETAILS_ERR]:", e)
        return { "version": None }


def sync_github_to_local():
    remote_files = fetch_repo_tree(GIT_D_PATH)

    normalized = []
    for f in remote_files:
        relative = f["path"].replace(GIT_D_PATH, "").lstrip("/")
        local = ospath.join(APP_DIR, relative)
        normalized.append({
            "github": f,
            "local_path": local,
            "relative": relative
        })

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
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = [
            executor.submit(download_file, github, local_path, relative)
            for github, local_path, relative in tasks
        ]
        for _ in as_completed(futures):
            pass  # just wait for all to finish

    # Step 2 — Delete missing files
    remote_set = {f["relative"] for f in normalized}

    for root, _, files in walk(APP_DIR):
        for file in files:
            full = ospath.join(root, file)
            relative = ospath.relpath(full, APP_DIR).replace("\\", "/")

            if relative not in remote_set:
                print("Deleting REMOVED file:", relative)
                remove(full)


def git_sha_of_file(path):
    from hashlib import sha1
    with open(path, "rb") as fp:
        data = fp.read()
    return sha1(f"blob {len(data)}\0".encode() + data).hexdigest()

def initiate_update():
    local_version = get_local_details().get("version", None)
    remote_version = get_remote_details().get("version", None)
    if remote_version is None:
        raise Exception("Could not fetch remote version.")
    
    if local_version != remote_version:
        sync_github_to_local()

if __name__ == "__main__":
    try:
        
        # sync_github_to_local()
        print(get_rate_limit())
        # print(ROOT_DIR)
        # print(APP_DIR)
        # print(get_local_details())
        # print(get_remote_details())
    except Exception as e:
        print(e)
