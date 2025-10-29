import tkinter as tk
from tkinter import ttk, messagebox
import csv
import os
import variables as v

# LOCALDATA = os.getenv("LOCALAPPDATA")
DATA_DIR = v.DATA_DIR()
STUDENT_CSV = v.STUDENT_CSV

BG_COLOR = "#1f1f1f"
BTN_COLOR = "#353434"
FONT_COLOR = "white"

ENTRY_WIDTH = 25   # uniform width for all fields

def register_window():
    root = tk.Tk()
    root.title("Register Student")
    root.geometry("400x450")
    root.configure(bg=BG_COLOR)

    frame = tk.Frame(root, bg=BG_COLOR)
    frame.pack(expand=True)

    def make_entry(label_text):
        tk.Label(frame, text=label_text, fg=FONT_COLOR, bg=BG_COLOR, font=("Arial", 12)).pack(pady=(10, 2))
        entry = tk.Entry(
            frame,
            font=("Arial", 16),
            width=ENTRY_WIDTH,
            bg="#2e2e2e",
            fg=FONT_COLOR,
            justify="center",
            insertbackground=FONT_COLOR
        )
        entry.pack()
        return entry

    # --- Student ID field ---
    sid_entry = make_entry("Student ID")
    firstname_entry = make_entry("Firstname")
    middlename_entry = make_entry("Middlename")
    lastname_entry = make_entry("Lastname")

    # --- Course dropdown ---
    tk.Label(frame, text="Course", fg=FONT_COLOR, bg=BG_COLOR, font=("Arial", 12)).pack(pady=(10, 2))
    courses = ["BSCS", "BSIT", "BSECE", "BSCE", "BSEE"]
    course_cb = ttk.Combobox(frame, values=courses, state="readonly", font=("Arial", 14), width=ENTRY_WIDTH-2)
    course_cb.pack()

    # --- Save button ---
    def save_student():
        sid = sid_entry.get().strip()
        fname = firstname_entry.get().strip()
        mname = middlename_entry.get().strip()
        lname = lastname_entry.get().strip()
        course = course_cb.get().strip()

        fields = [
            {"Student ID", sid},
        ]

        if not sid or not fname or not lname or not course:
            messagebox.showerror("Error", "Student ID, Firstname, Lastname, and Course are required!")
            return

        # Append student data into CSV
        with open(STUDENT_CSV, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([sid, lname, fname, mname, course])

        messagebox.showinfo("Success", f"Student registered!\nID: {sid}")
        root.destroy()

    tk.Button(frame, text="Save", command=save_student,
              font=("Arial", 14),
              bg=BTN_COLOR, fg=FONT_COLOR, width=ENTRY_WIDTH).pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    register_window()
