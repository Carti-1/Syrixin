import psutil

def get_battery():
    
    battery = psutil.sensors_battery()
    
    if battery is not None:
        return battery

def battery_status(battery):
    if battery is not None:
        if battery.power_plugged:
            return "Charging"
        else:
            return "On battery"