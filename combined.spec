# -*- mode: python ; coding: utf-8 -*-
import sys, os, shutil
from typing import Any, Literal

# --- Mode selection ---
user_input = input("In development? (y/N): ").strip()
dev_mode = user_input == "y"
if user_input == "N":
    if input("Type 'yes' to confirm production mode: ").strip().lower() != "yes":
        print("Production unconfirmed, exiting PyInstaller...")
        sys.exit(1)
elif not user_input == "y":
    print("Response unclear, exiting PyInstaller...")
    sys.exit(1)
print("In development..." if dev_mode else "CONFIRMED PRODUCTION")

# --- Script Configuration ---
# scripts = ["nl_Accessly", "nl_main", "nl_updater", "nl_cmd"]  # just edit this list anytime
# onefile_builds = ["nl_updater", "elevater"]   # these will be built as single .exe
scripts: list[dict[Literal["name", "hidden_imports", "one_file", "force_cmd"], Any]] = [
    {
        "name": "n_launcher",
        "hidden_imports": [
            "webview",
            "mylib.msgbx",
            "mylib.util",
            "mylib.env",
            "mylib.conn",
            "wsgiref.simple_server",
            "webview.http",
            "mylib.elevater",  # You're using this in run_elevated
            "psutil",
        ],
        "one_file": True,
        "force_cmd": False,
    },
    {"name": "n_services", "hidden_imports": [], "one_file": True, "force_cmd": False},
]  # just edit this list anytime
# onefile_builds = ["n_launcher", "n_services"]  # these will be built as single .exe
onefile_builds = [item["name"] for item in scripts if item.get("one_file", False)]
# forceCMD = ["nl_cmd"]
forceCMD = []
# PROJECT_NAME = "NizamLab"
# destination_folder = "src"
# SRC_DIR =  os.path.join(os.getcwd(), 'src')
SRC_DIR = os.path.join(os.getcwd(), "testing")
destination_folder = ""


block_cipher = None
exe_objects = []
binaries_all = []
datas_all = []
multifile_exes = []

# --- Generate Analysis + EXE dynamically ---
for app in scripts:
    script_path = os.path.join(SRC_DIR, f"{app['name']}.py")
    print(f"Building {app['name']}...")

    analysis = Analysis(  # type: ignore
        [script_path],
        pathex=[],
        binaries=[],
        datas=[],
        hiddenimports=app["hidden_imports"],
        hookspath=[],
        hooksconfig={},
        runtime_hooks=[],
        excludes=[],
        noarchive=False,
        optimize=0,
    )

    pyz = PYZ(analysis.pure)  # type: ignore

    # --- Single-file build (e.g. Updater) ---
    if app["one_file"]:
        exe = EXE(  # type: ignore
            pyz,
            analysis.scripts,
            analysis.binaries,
            analysis.datas,
            [],
            name=app["name"],
            debug=False,
            bootloader_ignore_signals=False,
            strip=False,
            upx=True,
            runtime_tmpdir=None,
            console=(dev_mode or app["force_cmd"]),
        )
        exe_objects.append(exe)

    # --- Normal multi-file build ---
    else:
        exe = EXE(  # type: ignore
            pyz,
            analysis.scripts,
            [],
            exclude_binaries=True,
            name=app["name"],
            debug=False,
            bootloader_ignore_signals=False,
            strip=True,
            upx=False,
            console=dev_mode,
        )
        exe_objects.append(exe)
        multifile_exes.append(exe)
        binaries_all += analysis.binaries
        datas_all += analysis.datas

# --- Collect ONLY multi-file builds ---
if multifile_exes:
    coll = COLLECT(  # type: ignore
        *multifile_exes,
        binaries_all,
        datas_all,
        strip=True,
        upx=True,
        name=destination_folder,
    )
else:
    print("No multi-file builds to collect")
# # --- Move one-file builds into project folder ---
# distpath = os.path.join(os.getcwd(), "dist")

# for exe in onefile_builds:
#     src = os.path.join(distpath, f"{exe}.exe")
#     dst = os.path.join(distpath, destination_folder, f"{exe}.exe")
#     if os.path.exists(src):
#         print(f"📁 Moving {exe}.exe → {dst}")
#         shutil.move(src, dst)
