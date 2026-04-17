import wmi

def get_monitor_device():
   moniter_devices = []
   w = wmi.WMI()
   for device in w.Win32_PnPEntity():
       if "MONITOR" in str(device.HardwareID).upper():
           moniter_devices.append({'Name': device.Name, 'HardwareID': list(device.HardwareID)})
   return moniter_devices   

if __name__ == "__main__":
   print(get_monitor_device())