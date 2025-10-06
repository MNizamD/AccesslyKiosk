import socket
import threading
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

HOST = ""      # Bind to all interfaces
PORT = 5050

class ServerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Class Server")
        self.master.geometry("400x200")
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

        tk.Label(master, text="Teacher ID:").pack()
        self.teacher_entry = tk.Entry(master)
        self.teacher_entry.pack(pady=5)

        tk.Label(master, text="Activity Name:").pack()
        self.activity_entry = tk.Entry(master)
        self.activity_entry.pack(pady=5)

        self.start_button = tk.Button(master, text="Start Class", command=self.start_server)
        self.start_button.pack(pady=10)

        self.status_label = tk.Label(master, text="Server not running", fg="red")
        self.status_label.pack(pady=10)

        self.server_socket = None
        self.is_running = False

    def start_server(self):
        teacher_id = self.teacher_entry.get().strip()
        activity = self.activity_entry.get().strip()

        if not teacher_id or not activity:
            messagebox.showerror("Error", "Please enter both Teacher ID and Activity Name.")
            return

        self.teacher_id = teacher_id
        self.activity = activity

        self.is_running = True
        self.status_label.config(text=f"Class active ({activity})", fg="green")
        threading.Thread(target=self.run_server, daemon=True).start()

    def run_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(5)
        print(f"[SERVER] Running on port {PORT}")

        while self.is_running:
            try:
                conn, addr = self.server_socket.accept()
                print(f"[CONNECT] Student from {addr}")
                conn.sendall(f"ACTIVE|{self.teacher_id}|{self.activity}|{datetime.now()}".encode())
                conn.close()
            except Exception as e:
                print("[ERR]", e)
                break

    def on_close(self):
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ServerApp(root)
    root.mainloop()
