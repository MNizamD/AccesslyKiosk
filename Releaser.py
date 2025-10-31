import os
import zipfile
import json
import shutil
from datetime import datetime

# ---------------- CONFIG ----------------
DETAILS_NAME = "details.json"
DETAILS_FILE = os.path.join("src", DETAILS_NAME)
DIST_FOLDER = "dist"
DIST_FOLDERS_TO_ZIP = [
    f"{DIST_FOLDER}/src",
    # "wexpect"
]  # include both folders under dist/
INSTALLER_FOLDER = "installer"
RELEASE_LATEST = os.path.join("releases", "latest", "download")
RELEASE_OLD = os.path.join("releases", "old_versions")
ZIP_BASENAME = "NizamLab"
MAX_OLD_VERSIONS = 5  # <--- keep only 5 old versions
# ----------------------------------------


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


def cleanup_old_versions():
    """Keep only the newest MAX_OLD_VERSIONS .zip files in RELEASE_OLD."""
    if not os.path.exists(RELEASE_OLD):
        return

    zip_files = [
        os.path.join(RELEASE_OLD, f)
        for f in os.listdir(RELEASE_OLD)
        if f.endswith(".zip")
    ]

    if len(zip_files) <= MAX_OLD_VERSIONS:
        return

    # Sort by modification time (oldest first)
    zip_files.sort(key=os.path.getmtime)

    # Delete oldest beyond the max limit
    to_delete = zip_files[:-MAX_OLD_VERSIONS]
    for path in to_delete:
        try:
            os.remove(path)
            print(f"[–] Deleted old version: {os.path.basename(path)}")
        except Exception as e:
            print(f"[!] Failed to delete {path}: {e}")


def make_zip(new_version: str):
    os.makedirs(RELEASE_LATEST, exist_ok=True)
    os.makedirs(RELEASE_OLD, exist_ok=True)

    zip_name = f"{ZIP_BASENAME}-{new_version}.zip"
    zip_path = os.path.join(RELEASE_LATEST, zip_name)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add dist folders
        for folder_name in DIST_FOLDERS_TO_ZIP:
            folder_path = os.path.realpath(folder_name)
            if not os.path.exists(folder_path):
                print(f"[!] Skipping missing folder: {folder_path}")
                continue

            for root, _, files in os.walk(folder_path):
                print(f"[+] Zipping: {root}")
                for file in files:
                    abs_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_path, DIST_FOLDER)
                    zf.write(abs_path, arcname=rel_path)

        # Add installer files
        if os.path.exists(INSTALLER_FOLDER):
            for file in os.listdir(INSTALLER_FOLDER):
                abs_path = os.path.join(INSTALLER_FOLDER, file)
                if os.path.isfile(abs_path):
                    print(f"[+] Zipping installer file: {file}")
                    zf.write(abs_path, arcname=file)

        # Add updated details.json
        print(f"[+] Zipping: {DETAILS_NAME}")
        zf.write(DETAILS_FILE, arcname=os.path.join("src", DETAILS_NAME))

    print(f"[✓] New release created: {zip_path}")
    return zip_path


def main():
    if not os.path.exists(DETAILS_FILE):
        raise FileNotFoundError("details.json not found!")

    with open(DETAILS_FILE, "r") as f:
        details = json.load(f)

    current_version = details["version"]
    print(f"Current version: {current_version}")

    # Ask user for bump type
    bump = input("Bump version? (mj=Major, mn=Minor, p=Patch): ").strip()
    new_version = bump_version(current_version, bump)

    # Move old release (if exists)
    old_zip = os.path.join(RELEASE_LATEST, f"{ZIP_BASENAME}-{current_version}.zip")
    if os.path.exists(old_zip):
        os.makedirs(RELEASE_OLD, exist_ok=True)
        new_old_path = os.path.join(RELEASE_OLD, f"{ZIP_BASENAME}-{current_version}.zip")
        shutil.move(old_zip, new_old_path)
        print(f"[~] Moved old release to {new_old_path}")

    # 🔹 Clean up older than 5 files
    cleanup_old_versions()

    # Update details.json
    details["version"] = new_version
    details["updated"] = datetime.now().strftime("%Y-%m-%d")
    with open(DETAILS_FILE, "w") as f:
        json.dump(details, f, indent=4)

    print(f"[+] Updated details.json -> {new_version}")

    # Make new release
    make_zip(new_version)


if __name__ == "__main__":
    main()
