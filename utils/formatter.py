
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
