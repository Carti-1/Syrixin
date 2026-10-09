import time
import os
import datetime
import argparse

from monitor.cpu import get_cpu_use
from monitor.memory import get_ram_use
from monitor.disk import get_disk_use
from monitor.battery import get_battery, battery_status
from models.system_info import SystemInfo
from utils.formatter import format_cpu, format_ram, format_disk, format_battery, display
from logs.logger import log_info, log_warning, log_error


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


def run_monitor(
    interval: int = 5,
    _collect=None,
    _check=None,
    _sleep=None,
    _clear=None,
    _battery_status=None,
) -> None:
    """Loop: clear → timestamp → collect → display → check_alerts → sleep.

    The underscore-prefixed parameters exist for testing only; production
    code never passes them.
    """
    _collect         = _collect         if _collect         is not None else collect_metrics
    _check           = _check           if _check           is not None else check_alerts
    _sleep           = _sleep           if _sleep           is not None else time.sleep
    _clear           = _clear           if _clear           is not None else (
        lambda: os.system('cls' if os.name == 'nt' else 'clear')
    )
    _battery_status  = _battery_status  if _battery_status  is not None else battery_status

    log_info("Syrixin started — beginning system data collection.")
    try:
        while True:
            try:
                _clear()
                ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"=== Syrixin Monitor — {ts} ===")

                cpu, ram, disk, battery = _collect()
                status = _battery_status(battery)
                system = SystemInfo(cpu, ram, disk, battery, status)

                display(system)
                _check(system)

                _sleep(interval)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                log_error(f"Unexpected error during monitoring cycle: {e}")
    except KeyboardInterrupt:
        log_info("Monitor stopped by user.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Syrixin system monitor")
    parser.add_argument(
        "--interval", type=int, default=5,
        help="Refresh interval in seconds (default: 5)"
    )
    args = parser.parse_args()
    run_monitor(interval=args.interval)
