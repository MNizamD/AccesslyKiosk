import os
import json
import shutil
from datetime import datetime
from pathlib import Path

# ---------------- CONFIG ----------------
ROOT_FOLDER = Path(os.getcwd())
DEV_FOLDER = ROOT_FOLDER / "testing"
PROD_FOLDER = ROOT_FOLDER / "dist"
DETAILS_NAME = "details.json"
DETAILS_FILE = ROOT_FOLDER / DEV_FOLDER / DETAILS_NAME
WEB_WALL_DEV = DEV_FOLDER / "web_wall"
WEB_WALL_PROD = PROD_FOLDER / "web_wall"
# ----------------------------------------


def delete_folder(folder_path: Path) -> bool:
    """
    Delete a folder and all its contents recursively

    Args:
        folder_path: Path to the folder to delete

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            print(f"[-] Deleted folder: {folder_path}")
        else:
            print(f"[!] Folder doesn't exist: {folder_path}")

        return True
    except Exception as e:
        print(f"[!] Failed to delete {folder_path}: {e}")
        return False


def copy_files(src_path: Path, dst_path: Path) -> bool:
    """
    Copy a file or folder (with subfolders/files) to a destination inside a folder

    Args:
        src: Source file or folder path
        dst: Destination folder path (the source will be placed inside this folder)

    Returns:
        bool: True if successful, False otherwise
    """
    try:

        # Ensure destination directory exists
        dst_path.mkdir(parents=True, exist_ok=True)

        if src_path.is_file():
            # Copy single file
            shutil.copy2(src_path, dst_path / src_path.name)
            print(f"[+] Copied file: {src_path} → {dst_path / src_path.name}")

        elif src_path.is_dir():
            # Copy entire directory with contents
            dest_dir = dst_path / src_path.name
            shutil.copytree(src_path, dest_dir, dirs_exist_ok=True)
            print(f"[+] Copied folder: {src_path} → {dest_dir}")

        else:
            print(f"[!] Source not found: {src_path}")
            return False

        return True

    except Exception as e:
        print(f"[!] Copy failed: {e}")
        return False


def bump_version(version: str, part: str) -> str:
    major, minor, patch = map(int, version.split("."))
    if part == "mj":
        major += 1
        minor, patch = 0, 0
    elif part == "mn":
        minor += 1
        patch = 0
    elif part == "p":
        patch += 1
    else:
        raise ValueError("Invalid bump type. Use mj/mn/p")
    return f"{major}.{minor}.{patch}"


def main():
    if not os.path.exists(DETAILS_FILE):
        raise FileNotFoundError("details.json not found!")

    with open(DETAILS_FILE, "r") as f:
        details = json.load(f)

    current_version = details["version"]
    print(f"Current version: {current_version}")

    # Ask user for bump type
    bump = input("Bump version? (mj=Major, mn=Minor, p=Patch): ").strip()

    if not delete_folder(WEB_WALL_PROD):
        return

    new_version = bump_version(current_version, bump)

    # Update details.json
    details["version"] = new_version
    details["updated"] = datetime.now().strftime("%Y-%m-%d")
    with open(DETAILS_FILE, "w") as f:
        json.dump(details, f, indent=4)

    print(f"[+] Updated details.json -> {new_version}")

    if copy_files(WEB_WALL_DEV, PROD_FOLDER) and copy_files(
        DETAILS_FILE, WEB_WALL_PROD
    ):
        print(f"[✓] New release created: {PROD_FOLDER}")
    # Make new release
    # make_zip(new_version)


if __name__ == "__main__":
    main()
