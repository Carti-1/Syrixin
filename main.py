from monitor.cpu import get_cpu_use
from monitor.memory import get_ram_use
from monitor.disk import get_disk_use
from monitor.battery import get_battery, battery_status
from models.system_info import SystemInfo
from utils.formatter import format_cpu, format_ram, format_disk, format_battery
from logs.logger import log_info, log_warning, log_error


def check_alerts(system: SystemInfo, log_warn=log_warning) -> list[str]:
    """Verifica limites e emite avisos. Retorna lista de mensagens geradas."""
    alerts = []

    cpu_str = format_cpu(system.cpu)
    ram_str = format_ram(system.ram)
    disk_str = format_disk(system.disk)
    battery_str = format_battery(system.battery, system.battery_status)

    if system.battery is None:
        msg = "Battery not available or not detected."
        log_warn(msg)
        alerts.append(msg)

    if system.cpu is not None and system.cpu > 90:
        msg = f"High CPU usage: {cpu_str}"
        log_warn(msg)
        alerts.append(msg)

    if system.ram is not None and system.ram.percent > 85:
        msg = f"High RAM usage: {ram_str}"
        log_warn(msg)
        alerts.append(msg)

    if system.disk is not None and system.disk.percent > 90:
        msg = f"Disk almost full: {disk_str}"
        log_warn(msg)
        alerts.append(msg)

    if system.battery is not None and system.battery.percent < 20 and not system.battery.power_plugged:
        msg = f"Low battery: {battery_str}"
        log_warn(msg)
        alerts.append(msg)

    return alerts


if __name__ == "__main__":
    log_info("Syrixin started — beginning system data collection.")

    try:
        cpu = get_cpu_use()
    except Exception as e:
        log_error(f"Failed to collect CPU data: {e}")
        cpu = None

    try:
        ram = get_ram_use()
    except Exception as e:
        log_error(f"Failed to collect RAM data: {e}")
        ram = None

    try:
        disk = get_disk_use()
    except Exception as e:
        log_error(f"Failed to collect disk data: {e}")
        disk = None

    try:
        battery = get_battery()
    except Exception as e:
        log_error(f"Failed to collect battery data: {e}")
        battery = None

    status = battery_status(battery)

    system = SystemInfo(cpu, ram, disk, battery, status)

    cpu_str = format_cpu(system.cpu)
    ram_str = format_ram(system.ram)
    disk_str = format_disk(system.disk)
    battery_str = format_battery(system.battery, status)

    print("CPU:", cpu_str)
    print("RAM:", ram_str)
    print("Disk:", disk_str)
    print("Battery:", battery_str)

    check_alerts(system)

    log_info("Data collection and display completed successfully.")
