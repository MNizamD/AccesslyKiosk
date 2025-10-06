import os
import zipfile
import json
import shutil
from datetime import datetime

# ---------------- CONFIG ----------------
DETAILS_NAME = "details.json"
DETAILS_FILE = os.path.join('src', DETAILS_NAME)
DIST_FOLDER = os.path.join("dist", "NizamLab")
INSTALLER_FOLDER = "installer"   # <--- NEW
RELEASE_LATEST = os.path.join("releases", "latest", "download")
RELEASE_OLD = os.path.join("releases", "old_versions")
ZIP_BASENAME = "NizamLab"
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

INSTALLER_FOLDER = "installer"  # add this at the top with other configs

def make_zip(new_version: str):
    os.makedirs(RELEASE_LATEST, exist_ok=True)
    os.makedirs(RELEASE_OLD, exist_ok=True)

    zip_name = f"{ZIP_BASENAME}-{new_version}.zip"
    zip_path = os.path.join(RELEASE_LATEST, zip_name)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add dist/NizamLab content (preserve structure under NizamLab/)
        for root, _, files in os.walk(DIST_FOLDER):
            print(f"[+] Zipping: {root}")
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, DIST_FOLDER)
                zf.write(abs_path, arcname=rel_path)

        # Add installer files (flat) into NizamLab/
        if os.path.exists(INSTALLER_FOLDER):
            for file in os.listdir(INSTALLER_FOLDER):
                abs_path = os.path.join(INSTALLER_FOLDER, file)
                if os.path.isfile(abs_path):  # only files
                    print(f"[+] Zipping: {abs_path}")
                    zf.write(abs_path, arcname=file)

        # Add updated details.json (overwrite inside NizamLab/)
        rel_path = os.path.relpath(abs_path, DIST_FOLDER)
        print(f"[+] Zipping: {DETAILS_NAME}")
        zf.write(DETAILS_FILE, arcname=DETAILS_NAME)

    print(f"[+] New release created: {zip_path}")
    return zip_path


def main():
    # Load details.json
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
