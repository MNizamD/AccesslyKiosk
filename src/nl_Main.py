# import tkinter as tk
from csv import reader as rd, writer as wt
from os import path as ospath, remove as rm
from datetime import datetime
from lib.util import check_admin, get_details_json, is_process_running, run_elevated, showToFronBackEnd
from lib.env import get_pc_name, ONLY_USER, get_env
from time import sleep
# ================= CONFIG ==================

env = get_env()
CHECK_INTERVAL = 15

def check_files():
    # Ensure log file exists
    LOG_FILE = env.log_file
    if ospath.exists(LOG_FILE):
        return
    try: # Since log does not exists.
        with open(LOG_FILE, mode="w", newline="") as file:
            writer = wt(file)
            writer.writerow(["StudentID", "PC_Name", "Login_Time", "Logout_Time"])
    except:
        raise Exception("Log file error.")


# Load student IDs
def load_students() -> dict[str, str]:
    students = {"iamadmin": "Admin"}
    STUDENT_CSV = env.student_csv
    if ospath.exists(STUDENT_CSV):
        with open(STUDENT_CSV, mode="r", newline="") as file:
            reader = rd(file)
            for row in reader:
                if len(row) >= 1:
                    students[row[0]] = row[1] if len(row) > 1 else ""
    return students

BG_COLOR = "#1f1f1f"
BTN_COLOR = "#353434"
FONT_COLOR = "white"
SECONDARY_FONT_COLOR = "#aaaaaa"


# ================= APP =====================
class KioskApp:
    FLAG_IDLE_FILE = env.flag_idle_file
    def __init__(self, master):
        from tkinter import Frame, Label, Entry
        self.reset_idle_timer()

        self.master = master
        self.master.title("Lab Access")
        self.master.attributes('-fullscreen', True)  # Fullscreen at start
        self.master.attributes('-topmost', True)
        self.master.configure(bg=BG_COLOR)
        self.master.attributes("-alpha", 0.95)
        self.master.protocol("WM_DELETE_WINDOW", self.disable_event)

        self.student_id = None
        self.login_time = None

        # --- Outer frame fills the window and centers content ---
        self.frame = Frame(master, bg=BG_COLOR)
        self.frame.pack(fill="both", expand=True)

        # Use grid layout to center everything
        self.frame.grid_rowconfigure(0, weight=1)  # Top spacer
        self.frame.grid_rowconfigure(1, weight=0)  # PC Name
        self.frame.grid_rowconfigure(2, weight=0)  # Instruction
        self.frame.grid_rowconfigure(3, weight=0)  # Entry field
        self.frame.grid_rowconfigure(4, weight=1)  # Bottom spacer
        self.frame.grid_columnconfigure(0, weight=1)  # Center horizontally

        # --- PC Name ---
        self._PC_NAME = get_pc_name()
        self._ALLOWED_STUDENTS = load_students()
        self.pc_label = Label(
            self.frame,
            text=self._PC_NAME,
            font=("Arial", 48, "bold"),
            fg=FONT_COLOR,
            bg=BG_COLOR,
        )
        self.pc_label.grid(row=1, column=0, pady=(0, 20))

        # --- Instruction ---
        self.label = Label(
            self.frame,
            text="Enter Student ID to access this PC",
            font=("Arial", 15),
            fg=FONT_COLOR,
            bg=BG_COLOR,
        )
        self.label.grid(row=2, column=0, pady=(0, 20))

        # --- Entry field ---
        self.entry = Entry(
            self.frame,
            font=("Arial", 22),
            bg="#2e2e2e",
            fg=FONT_COLOR,
            justify="center",
            insertbackground=FONT_COLOR,
        )
        self.entry.grid(row=3, column=0, pady=(0, 20))
        self.entry.focus()

        # Bind Enter key to login
        self.entry.bind("<Return>", lambda event: self.login())
        # Bind key release to dynamically mask non-digit input
        self.entry.bind("<KeyRelease>", self.check_input_mask)
        self.entry.bind("<Key>", self.reset_idle_timer)   # <--- NEW

        ### --- Version/Update Info ---
        details = get_details_json(env) or {"version": "?", "updated": "?"}
        self.version_label = Label(
            self.frame,
            text=f"v{details.get('version','?')}  |  Updated: {details.get('updated','?')}",
            font=("Arial", 10),
            fg=SECONDARY_FONT_COLOR,
            bg=BG_COLOR
        )
        self.version_label.grid(row=4, column=0, pady=(10, 5), sticky="s")

         # Start idle checker
        self.check_idle()

    def reset_idle_timer(self, event=None):
        """Called whenever there is keyboard input"""
        self.last_activity = datetime.now()
        # Remove idle flag if it exists (user is active)
        self.remove_idle()

    def check_idle(self):
        """Check every second if user has been idle > 60s"""
        elapsed = (datetime.now() - self.last_activity).seconds
        if elapsed >= CHECK_INTERVAL:  # idle threshold
            self.write_idle()
            # print("Idle")
        # else:
            # print("Busy")
        # recheck every second
        self.master.after(1000, self.check_idle)
    
    def write_idle(self):
        if not ospath.exists(self.FLAG_IDLE_FILE):
            with open(self.FLAG_IDLE_FILE, "w") as f:
                f.write("IDLE")

    def remove_idle(self):
        if ospath.exists(self.FLAG_IDLE_FILE):
            rm(self.FLAG_IDLE_FILE)

    # Disable closing
    def disable_event(self):
        pass

    # Mask input if it contains non-digit characters
    def check_input_mask(self, event=None):
        text = self.entry.get()
        if text and not text.isdigit():
            self.entry.config(show="*")
        else:
            self.entry.config(show="")

    # Login logic
    def login(self):
        from tkinter import END
        sid = self.entry.get().strip()
        if sid == "destruct":
            self.master._should_restart = False
            self.destruct()
            return
        
        if sid == "cmd" or sid.startswith("cmd "):
            # Allow console to appear on top
            self.entry.delete(0, END)
            self.master.attributes('-topmost', False)
            self.master.update()  # apply immediately

            # Launch your CLI process
            args = " ".join(sid.split()[1:])
            default_arg = f"--user {ONLY_USER}"
            def check_cmd():
                CMD_FILE_NAME = env.__CMD_FILE_NAME
                result= is_process_running(CMD_FILE_NAME)
                if result.running:
                    print(f"[{result.data["pid"]}] {CMD_FILE_NAME} is still running {result.data["exe"]}")
                    self.master.after(1000, check_cmd)
                else:
                    # CLI has closed → restore topmost
                    print("CLI has stopped")
                    self.master.attributes('-topmost', True)
                    self.master.update()  # apply immediately

            run_elevated(f"{env.script_cmd} {default_arg if sid=="cmd" else args}")
            sleep(3)
            # Start polling for process exit
            check_cmd()
            return

        if sid not in self._ALLOWED_STUDENTS:
            from tkinter.messagebox import showerror
            showerror("Access Denied", "Invalid Student ID!")
            self.entry.delete(0, END)
            return

        self.student_id = sid
        self.login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Log login
        LOG_FILE = env.log_file
        with open(LOG_FILE, mode="a", newline="") as file:
            writer = wt(file)
            writer.writerow([self.student_id, self._PC_NAME, self.login_time, ""])

        # Switch to logged-in view
        self.remove_idle()
        
        self.show_logged_in()

    def destruct(self):
        self.remove_idle()
        self.master.destroy()

    def show_logged_in(self):
        from tkinter import Label, Button
        # Shrink window to normal size
        self.master.attributes("-fullscreen", False)
        self.master.geometry("280x130")
        self.master.resizable(False, False)

        # Clear screen
        for widget in self.frame.winfo_children():
            widget.destroy()
            
        self.student_id = self.student_id or 'Unknown'

        welcome_label = Label(
            self.frame,
            text=f"Welcome {self._ALLOWED_STUDENTS[self.student_id] or self.student_id}",
            font=("Arial", 12),
            fg=FONT_COLOR,
            bg=BG_COLOR,
        )
        welcome_label.pack(pady=5)

        self.logout_button = Button(
            self.frame,
            text="Logout",
            font=("Arial", 12),
            fg=FONT_COLOR,
            bg=BTN_COLOR,
            command=self.logout,
        )
        self.logout_button.pack(pady=10)

        # Duration label (starts at 0s)
        self.status_label = Label(
            self.frame,
            text="Logged in: 0s",
            font=("Arial", 10),
            fg=FONT_COLOR,
            bg=BG_COLOR,
        )
        self.status_label.pack(pady=2)

        # Start updating duration
        self.start_time = datetime.now()
        self.update_duration()

    def update_duration(self):
        """Update the duration label every second"""
        elapsed = (datetime.now() - self.start_time).seconds
        mins, secs = divmod(elapsed, 60)
        hrs, mins = divmod(mins, 60)

        if hrs > 0:
            time_str = f"Logged in: {hrs}h {mins}m {secs}s"
        elif mins > 0:
            time_str = f"Logged in: {mins}m {secs}s"
        else:
            time_str = f"Logged in: {secs}s"

        # Keep updating until logout
        if self.logout_button["state"] != "disabled":
            self.status_label.config(text=time_str)
            self.master.after(1000, self.update_duration)

    def logout(self):
        logout_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Update last empty logout field
        rows = []
        LOG_FILE = env.log_file
        with open(LOG_FILE, mode="r", newline="") as file:
            reader = list(rd(file))
            rows = reader

        for i in range(len(rows) - 1, -1, -1):
            if rows[i][0] == self.student_id and rows[i][3] == "":
                rows[i][3] = logout_time
                break

        with open(LOG_FILE, mode="w", newline="") as file:
            writer = wt(file)
            writer.writerows(rows)

        # Show logout message instead of timer
        self.status_label.config(text="You have successfully logged out!")

        # Disable the button to prevent double clicks
        self.logout_button.config(state="disabled")

        # After 3 seconds, destroy
        self.master.after(3000, lambda: (self.destruct()))


def run():
    from tkinter import Tk
    check_admin("main")
    root = Tk()
    root.title("Accessly UI")
    # app = KioskApp(root)
    KioskApp(root)
    setattr(root, '_should_restart', True)  # mark flag
    root.mainloop()
    
    # Return True if flagged for restart
    return getattr(root, "_should_restart", False)


# ================= RUN =====================
if __name__ == "__main__":
    from sys import exit
    try:
        check_files()
        while True:
            should_restart = run()
            if not should_restart:
                break  # exit cleanly
            print("Restarting...")
    except Exception as e:
        showToFronBackEnd("Main Error", "Main UI error.", str(e))
        exit(369)
    else:
        exit(0)

