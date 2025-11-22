import sys, os
from pathlib import Path

# --- Determine base directory ---
if getattr(sys, "frozen", False):
    base_dir = getattr(sys, "_MEIPASS")  # PyInstaller temp folder
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

# --- Add base directory to sys.path ---
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

# --- Dynamically add all immediate subdirectories ---
for sub in Path(base_dir).iterdir():
    if sub.is_dir() and str(sub) not in sys.path:
        sys.path.insert(0, str(sub))
