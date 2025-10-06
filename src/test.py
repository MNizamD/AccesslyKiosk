import subprocess
import os

# The input values, joined by newlines (like typing them)
fulluser = f"{os.environ['COMPUTERNAME']}\\{os.environ['USERNAME']}"
appdata = os.environ['APPDATA']
answers = "iamadmin\n"

# Run the target script and send the answers to its stdin
subprocess.run(
    ["runas ", "/savecred /user:Administrator", f"{appdata}\\NizamLab\\Main.exe"],  # or ["py", "script.py"] on Windows
    # input=answers,
    text=True
)
