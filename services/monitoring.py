from logs.logger import log_error
from monitor.cpu import get_cpu_use, get_cpu_temperature
from monitor.memory import get_ram_use
from monitor.disk import get_disk_use
from monitor.battery import get_battery, battery_status
from models.system_info import SystemInfo

def collect_metrics(log_err=log_error, _battery_status=battery_status, _cpu_interval=1):
    """Collect each system metric independently, storing None on failure.

    Returns a tuple (cpu, ram, disk, battery).  A failed collector stores
    None for that metric and calls log_err with the error message; the
    remaining collectors still run.

    _battery_status is accepted but not called here; it exists so callers
    that inject collect_metrics can also inject battery_status for testing.
    """
    try:
        cpu = get_cpu_use(interval=_cpu_interval)
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
    # A shorter sampling window makes the desktop's one-second refresh feel
    # responsive while the terminal monitor keeps its original CPU interval.
    cpu, ram, disk, battery = collect_metrics(log_err=log_err, _cpu_interval=0.25)
    status = battery_status(battery)
    try:
        cpu_temp = get_cpu_temperature()
    except Exception as e:
        log_err(f"Failed to collect CPU temperature: {e}")
        cpu_temp = None

    return SystemInfo(
        cpu=cpu,
        ram=ram,
        disk=disk,
        battery=battery,
        battery_status=status,
        cpu_temp=cpu_temp,
    )
