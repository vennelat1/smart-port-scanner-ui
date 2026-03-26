import socket
import threading
import json
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import time

COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
    53: "DNS", 80: "HTTP", 110: "POP3", 143: "IMAP",
    443: "HTTPS", 3306: "MySQL", 8080: "HTTP-Proxy"
}

results = []
lock = threading.Lock()
scan_active = False

# -------- Core Logic --------
def scan_port(ip, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False


def get_service(ip, port):
    try:
        sock = socket.socket()
        sock.settimeout(1)
        sock.connect((ip, port))
        banner = sock.recv(1024).decode(errors="ignore").strip()
        sock.close()
        return banner if banner else COMMON_PORTS.get(port, "Unknown")
    except:
        return COMMON_PORTS.get(port, "Unknown")


def scan_worker(ip, port, tree):
    global scan_active
    if not scan_active:
        return

    if scan_port(ip, port):
        service = get_service(ip, port)
        result = {"port": port, "service": service}
        with lock:
            results.append(result)
        tree.insert("", "end", values=(port, service))

        # simulate stealth delay
        time.sleep(0.05)


def start_scan(target, port_range, tree, status_label, progress):
    global scan_active
    scan_active = True

    try:
        ip = socket.gethostbyname(target)
    except:
        messagebox.showerror("Error", "Invalid target")
        return

    for row in tree.get_children():
        tree.delete(row)
    results.clear()

    start_port, end_port = map(int, port_range.split('-'))
    ports = list(range(start_port, end_port + 1))

    progress['maximum'] = len(ports)
    progress['value'] = 0

    status_label.config(text=f"Scanning {ip}...")
    start_time = datetime.now()

    def update_progress():
        progress['value'] += 1

    threads = []
    for port in ports:
        t = threading.Thread(target=lambda p=port: [scan_worker(ip, p, tree), update_progress()])
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    end_time = datetime.now()
    status_label.config(text=f"Completed in {end_time - start_time}")
    scan_active = False


def stop_scan(status_label):
    global scan_active
    scan_active = False
    status_label.config(text="Scan Stopped")


def save_results():
    with open("scan_report.json", "w") as f:
        json.dump(results, f, indent=4)
    messagebox.showinfo("Saved", "Results saved")

# -------- GUI --------
def create_gui():
    root = tk.Tk()
    root.title("Elite Port Scanner")
    root.geometry("800x550")
    root.configure(bg="#0d1117")

    style = ttk.Style()
    style.theme_use("default")
    style.configure("Treeview", background="#161b22", foreground="white", fieldbackground="#161b22")

    frame = tk.Frame(root, bg="#0d1117")
    frame.pack(pady=10)

    tk.Label(frame, text="Target:", fg="white", bg="#0d1117").grid(row=0, column=0)
    target_entry = tk.Entry(frame, width=20, bg="#161b22", fg="white")
    target_entry.grid(row=0, column=1)

    tk.Label(frame, text="Ports:", fg="white", bg="#0d1117").grid(row=0, column=2)
    port_entry = tk.Entry(frame, width=15, bg="#161b22", fg="white")
    port_entry.insert(0, "1-100")
    port_entry.grid(row=0, column=3)

    tree = ttk.Treeview(root, columns=("Port", "Service"), show="headings")
    tree.heading("Port", text="Port")
    tree.heading("Service", text="Service")
    tree.pack(fill="both", expand=True, pady=10)

    progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
    progress.pack(pady=5)

    status_label = tk.Label(root, text="Idle", fg="white", bg="#0d1117")
    status_label.pack()

    btn_frame = tk.Frame(root, bg="#0d1117")
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Start", command=lambda: threading.Thread(
        target=start_scan,
        args=(target_entry.get(), port_entry.get(), tree, status_label, progress)
    ).start(), bg="#238636", fg="white").grid(row=0, column=0, padx=5)

    tk.Button(btn_frame, text="Stop", command=lambda: stop_scan(status_label), bg="#da3633", fg="white").grid(row=0, column=1, padx=5)

    tk.Button(btn_frame, text="Save", command=save_results, bg="#1f6feb", fg="white").grid(row=0, column=2, padx=5)

    root.mainloop()


if __name__ == "__main__":
    create_gui()
