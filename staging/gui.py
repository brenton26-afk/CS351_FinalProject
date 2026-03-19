import tkinter as tk
from tkinter import messagebox
import threading
import shutil
import os
import sys

drive = sys.argv[1]

root = tk.Tk()
root.title("USB Sync")

cancel_flag = False

def cancel_sync():
    global cancel_flag
    cancel_flag = True

def start_sync():
    thread = threading.Thread(target=sync_process)
    thread.start()

def sync_process():
    global cancel_flag
    
    total_size = get_folder_size(drive)
    free_space = shutil.disk_usage("C:/").free

    if total_size > free_space:
        messagebox.showerror("Error", "Not enough disk space.")
        return

    staging = f"C:/staging/{os.path.basename(drive)}"
    os.makedirs(staging, exist_ok=True)

    for root_dir, dirs, files in os.walk(drive):
        for file in files:
            if cancel_flag:
                shutil.rmtree(staging, ignore_errors=True)
                messagebox.showinfo("Cancelled", "Sync cancelled.")
                return

            src = os.path.join(root_dir, file)
            dst = os.path.join(staging, os.path.relpath(src, drive))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)

    # call your S3 sync function here
    messagebox.showinfo("Done", "Sync completed.")

def get_folder_size(folder):
    total = 0
    for root_dir, dirs, files in os.walk(folder):
        for f in files:
            fp = os.path.join(root_dir, f)
            total += os.path.getsize(fp)
    return total

tk.Label(root, text="USB detected. Sync this device?").pack()

tk.Button(root, text="Yes", command=start_sync).pack()
tk.Button(root, text="No", command=root.destroy).pack()
tk.Button(root, text="Cancel Sync", command=cancel_sync).pack()

root.mainloop()
