# -*- mode: python ; coding: utf-8 -*-
import sys, os, shutil

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
scripts = ["LockDown", "Main", "Updater"]  # just edit this list anytime
onefile_builds = ["Updater"]               # these will be built as single .exe
project_name = "NizamLab"
SRC_DIR =  os.path.join(os.getcwd(), 'src')


block_cipher = None
exe_objects = []
binaries_all = []
datas_all = []

# --- Generate Analysis + EXE dynamically ---
for name in scripts:
    script_path = os.path.join(SRC_DIR, f"{name}.py")
    print(f"Building {name}...")

    analysis = Analysis(
        [script_path],
        pathex=[],
        binaries=[],
        datas=[],
        hiddenimports=[],
        hookspath=[],
        hooksconfig={},
        runtime_hooks=[],
        excludes=[],
        noarchive=False,
        optimize=0,
    )

    pyz = PYZ(analysis.pure)

    # --- Single-file build (e.g. Updater) ---
    if name in onefile_builds:
        exe = EXE(
            pyz,
            analysis.scripts,
            analysis.binaries,
            analysis.datas,
            [],
            name=name,
            debug=False,
            bootloader_ignore_signals=False,
            strip=False,
            upx=True,
            runtime_tmpdir=None,
            console=dev_mode,
        )
        exe_objects.append(exe)

    # --- Normal multi-file build ---
    else:
        exe = EXE(
            pyz,
            analysis.scripts,
            [],
            exclude_binaries=True,
            name=name,
            debug=False,
            bootloader_ignore_signals=False,
            strip=True,
            upx=True,
            console=dev_mode,
        )
        exe_objects.append(exe)
        binaries_all += analysis.binaries
        datas_all += analysis.datas

# --- Collect multi-file builds into one folder ---
coll = COLLECT(
    *[exe for exe in exe_objects if exe.name not in onefile_builds],
    binaries_all,
    datas_all,
    strip=True,
    upx=True,
    name=project_name,
)

# --- Move one-file builds into project folder ---
distpath = os.path.join(os.getcwd(), 'dist')
singleFiles = [
    r'C:\Users\Marohom\Documents\NizamLab\src\elevater.py'
]

for exe in onefile_builds:
    src = os.path.join(distpath, f'{exe}.exe')
    dst = os.path.join(distpath, project_name, f'{exe}.exe')
    if os.path.exists(src):
        print(f"📁 Moving {exe}.exe → {dst}")
        shutil.move(src, dst)

# for file in singleFiles:
#     filename = file.split("\\").pop()
#     src = file
#     dst = os.path.join(distpath, project_name, filename)
#     if os.path.exists(src):
#         print(f"📁 Moving {filename} → {dst}")
#         shutil.copy(src, dst)

elevater = r'C:\Users\Marohom\Documents\NizamLab\src\elevater.py'
if os.path.exists(elevater):
    filename = 'elevater.py'
    e_dst = os.path.join(distpath, project_name, '_internal', filename)
    print(f"📁 Copying elevater → {e_dst}")
    shutil.copy(elevater, e_dst)
else:
    print(f'File not found: {elevater}')