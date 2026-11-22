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

def format_temperature(value):
    if value is None:
        return "N/A"
    return f"{value:.0f} °C"

def format_ram(ram):
    if ram is None:
        return "N/A"
    available = getattr(ram, "available", None)
    used = ram.total - available if available is not None else None
    return format_ram_values(ram.total, ram.percent, used)


def format_ram_values(total, percent, used=None):
    """Show total capacity, utilization, and used physical memory."""
    if used is None and total is not None and percent is not None:
        used = round(total * percent / 100)
    return (
        f"{format_gigabytes(total)} / {format_gigabytes(used)} "
        f"({format_value(percent, '%')})"
    )

def format_disk(disk):
    if disk is None:
        return "N/A"
    return (
        f"{format_gigabytes(disk.total)} / {format_gigabytes(disk.used)} "
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
        timestamp, cpu, ram_total, ram_pct, disk_used, disk_total, disk_pct, battery_pct, power_plugged = row[:9]
        cpu_temp = row[9] if len(row) > 9 else None
        ram_used = row[10] if len(row) > 10 else None

        cpu_text = format_cpu(cpu)
        ram_text = format_ram_values(ram_total, ram_pct, ram_used)
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
            f"Disco: {disk_text} | Bateria: {battery_text} | "
            f"Temperatura CPU: {format_temperature(cpu_temp)}"
        )

    return "\n".join(lines)
