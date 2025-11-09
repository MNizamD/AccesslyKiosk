# ================= Tkinter UI =================
class UpdateWindow:
    def disable_event(self):
        print("Surpressed close")

    def __init__(self):
        from tkinter import Tk, Label
        self.root = Tk()
        self.root.title("Updater")
        self.root.geometry("400x150")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.disable_event)

        self.label = Label(self.root, text="Waiting...", font=("Arial", 12))
        self.label.pack(pady=15)

        from tkinter.ttk import Progressbar
        self.progress = Progressbar(self.root, length=300, mode="determinate")
        self.progress.pack(pady=10)

        self.percent_label = Label(self.root, text="0%", font=("Arial", 10))
        self.percent_label.pack(pady=5)

        self.root.update()

    def set_message(self, msg):
        self.label.config(text=msg)
        self.root.update()

    def set_progress(self, percent: float):
        self.progress["value"] = percent
        self.percent_label.config(text=f"{int(percent)}%")
        self.root.update()

    def close(self):
        self.root.destroy()
# ==============================================

if __name__ == "__main__":
    ui = UpdateWindow()
    ui.set_message("Test")
    from time import sleep
    for i in range(100):
        ui.set_progress(i)
        sleep(.25)
    ui.close()