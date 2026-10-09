from models.system_info import SystemInfo


def format_cpu(cpu):
    if cpu is None:
        return "N/A"
    return f"{cpu}%"

def format_ram(ram):
    if ram is None:
        return "N/A"
    total = ram.total / (1024**3)
    return f"{total:.2f} GB / {ram.percent}%"

def format_disk(disk):
    if disk is None:
        return "N/A"
    use = disk.used / (1024**3)
    total = disk.total / (1024**3)
    return f"{use:.2f} GB / {total:.2f} GB ({disk.percent}%)"

def format_battery(battery, status):
    if battery is None:
        return "N/A"
    return f"{battery.percent}% / {status}"


def display(system: SystemInfo) -> None:
    """Print the four formatted metric lines for a SystemInfo snapshot."""
    print("CPU:", format_cpu(system.cpu))
    print("RAM:", format_ram(system.ram))
    print("Disk:", format_disk(system.disk))
    print("Battery:", format_battery(system.battery, system.battery_status))
