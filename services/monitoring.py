from logs.logger import log_error
from monitor.cpu import get_cpu_use
from monitor.memory import get_ram_use
from monitor.disk import get_disk_use
from monitor.battery import get_battery, battery_status
from models.system_info import SystemInfo

def collect_metrics(log_err=log_error, _battery_status=battery_status):
    """Collect each system metric independently, storing None on failure.

    Returns a tuple (cpu, ram, disk, battery).  A failed collector stores
    None for that metric and calls log_err with the error message; the
    remaining collectors still run.

    _battery_status is accepted but not called here; it exists so callers
    that inject collect_metrics can also inject battery_status for testing.
    """
    try:
        cpu = get_cpu_use()
    except Exception as e:
        log_err(f"Failed to collect CPU data: {e}")
        cpu = None

    try:
        ram = get_ram_use()
    except Exception as e:
        log_err(f"Failed to collect RAM data: {e}")
        ram = None

    try:
        disk = get_disk_use()
    except Exception as e:
        log_err(f"Failed to collect disk data: {e}")
        disk = None

    try:
        battery = get_battery()
    except Exception as e:
        log_err(f"Failed to collect battery data: {e}")
        battery = None

    return cpu, ram, disk, battery

def collect_system_info(log_err=log_error):
    cpu, ram, disk, battery = collect_metrics(log_err=log_err)
    status = battery_status(battery)

    return SystemInfo(
        cpu=cpu,
        ram=ram,
        disk=disk,
        battery=battery,
        battery_status=status,
    )