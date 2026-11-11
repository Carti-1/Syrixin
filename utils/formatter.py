from models.system_info import SystemInfo


def format_value(value, suffix=""):
    """Format a metric value, showing N/A when it is unavailable."""
    if value is None:
        return "N/A"
    return f"{value}{suffix}"


def format_gigabytes(value):
    """Convert a byte value to a readable GB string."""
    if value is None:
        return "N/A"
    return f"{value / (1024 ** 3):.2f} GB"


def format_cpu(cpu):
    if cpu is None:
        return "N/A"
    return f"{cpu}%"

def format_ram(ram):
    if ram is None:
        return "N/A"
    return f"{format_gigabytes(ram.total)} / {format_value(ram.percent, '%')}"

def format_disk(disk):
    if disk is None:
        return "N/A"
    return (
        f"{format_gigabytes(disk.used)} / {format_gigabytes(disk.total)} "
        f"({format_value(disk.percent, '%')})"
    )

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


def format_history(rows):
    if not rows:
        return "Nenhum registro de métricas encontrado."

    lines = []

    for row in rows:
        timestamp, cpu, ram_total, ram_pct, disk_used, disk_total, disk_pct, battery_pct, power_plugged = row

        cpu_text = format_cpu(cpu)
        ram_text = (
            f"{format_gigabytes(ram_total)} total "
            f"({format_value(ram_pct, '%')})"
        )
        disk_text = (
            f"{format_gigabytes(disk_used)} / {format_gigabytes(disk_total)} "
            f"({format_value(disk_pct, '%')})"
        )

        if power_plugged is None:
            power_text = "energia: N/A"
        elif power_plugged:
            power_text = "conectado à energia"
        else:
            power_text = "desconectado da energia"

        battery_text = f"{format_value(battery_pct, '%')} ({power_text})"
        lines.append(
            f"{timestamp} | CPU: {cpu_text} | RAM: {ram_text} | "
            f"Disco: {disk_text} | Bateria: {battery_text}"
        )

    return "\n".join(lines)
