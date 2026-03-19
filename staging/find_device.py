import wmi
import subprocess

c = wmi.WMI()

watcher = c.Win32_VolumeChangeEvent.watch_for(notification_type="Creation")

while True:
    event = watcher()
    
    drive_letter = event.DriveName
    print("Volume event detected:", drive_letter)

    # Now query logical disk for drive type
    for disk in c.Win32_LogicalDisk(DeviceID=drive_letter):
        if disk.DriveType == 2:  # 2 = Removable
            print("Removable USB detected:", drive_letter)
            subprocess.Popen([
        r"C:/Python312/python.exe",
        r"C:/Users/aidan/OneDrive/Documents/CS-351/PROJECT/gui.py",
        event.DriveName])
