import os
from requests import get

GIT_OWNER = "MNizamD"
GIT_REPO = "AccesslyKiosk"
GIT_D_PATH = "testing/web_wall"

LOCAL_PATH = "app_folder/web_wall"


def fetch_repo_tree(path):
    """Recursively fetch full GitHub folder tree."""
    url = f"https://api.github.com/repos/{GIT_OWNER}/{GIT_REPO}/contents/{path}"
    r = get(url)
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


def sync_github_to_local():
    # Fetch the remote file list
    remote_files = fetch_repo_tree(GIT_D_PATH)

    # Convert GitHub paths (testing/web_wall/...) to local paths (app_folder/web_wall/...)
    normalized = []
    for f in remote_files:
        relative = f["path"].replace(GIT_D_PATH, "").lstrip("/")
        local = os.path.join(LOCAL_PATH, relative)
        normalized.append({
            "github": f,
            "local_path": local,
            "relative": relative
        })

    # Ensure directories exist
    for f in normalized:
        os.makedirs(os.path.dirname(f["local_path"]), exist_ok=True)

    # Step 1 — Download missing or changed files
    for f in normalized:
        if not os.path.exists(f["local_path"]):
            print("Downloading NEW file:", f["relative"])
            content = get(f["github"]["download_url"]).content
            with open(f["local_path"], "wb") as fp:
                fp.write(content)
            continue

        # Compare sha: fast and reliable
        local_sha = git_sha_of_file(f["local_path"])
        if local_sha != f["github"]["sha"]:
            print("Updating CHANGED file:", f["relative"])
            content = get(f["github"]["download_url"]).content
            with open(f["local_path"], "wb") as fp:
                fp.write(content)

    # Step 2 — Delete files no longer on GitHub
    remote_set = {f["relative"] for f in normalized}
    # for root, dirs, files in os.walk(LOCAL_PATH):
    for root, _, files in os.walk(LOCAL_PATH):
        for file in files:
            full = os.path.join(root, file)
            relative = os.path.relpath(full, LOCAL_PATH)
            if relative not in remote_set:
                print("Deleting REMOVED file:", relative)
                os.remove(full)


def git_sha_of_file(path):
    """Calculate GitHub-like SHA for file content."""
    import hashlib
    data = open(path, "rb").read()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


if __name__ == "__main__":
    sync_github_to_local()
