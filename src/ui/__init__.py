import os, sys

# --- Fix import path for both .py and compiled .exe ---
# Detect whether we are in a PyInstaller bundle
if getattr(sys, 'frozen', False):
    base_dir = getattr(sys, '_MEIPASS')  # Safe access
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))


# Add that base directory to sys.path if not already there
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)
# -------------------------------------------------------