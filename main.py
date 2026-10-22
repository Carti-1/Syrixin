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
from storage.database import Database


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
    """Verify limits & send warnings. Return list of generated messages.

    Each metric is formatted only when its threshold is exceeded,
    avoiding unnecessary work when all values are within normal range.
    """
    alerts = []

    if system.battery is None:
        msg = "Battery not available or not detected."
        log_warn(msg)
        alerts.append(msg)

    if system.cpu is not None and system.cpu > 90:
        msg = f"High CPU usage: {format_cpu(system.cpu)}"
        log_warn(msg)
        alerts.append(msg)

    if system.ram is not None and system.ram.percent > 85:
        msg = f"High RAM usage: {format_ram(system.ram)}"
        log_warn(msg)
        alerts.append(msg)

    if system.disk is not None and system.disk.percent > 90:
        msg = f"Disk almost full: {format_disk(system.disk)}"
        log_warn(msg)
        alerts.append(msg)

    if system.battery is not None and system.battery.percent < 20 and not system.battery.power_plugged:
        msg = f"Low battery: {format_battery(system.battery, system.battery_status)}"
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

    database = Database("syrixin.db")
    try:
        log_info("Syrixin started — beginning system data collection.")
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
                database.save(system)

                _sleep(interval)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                log_error(f"Unexpected error during monitoring cycle: {e}")
                _sleep(interval)
    except KeyboardInterrupt:
        log_info("Monitor stopped by user.")

    finally:
        database.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Syrixin system monitor")
    parser.add_argument(
        "--interval", type=int, default=5,
        help="Refresh interval in seconds (default: 5, minimum: 1)"
    )
    args = parser.parse_args()
    if args.interval < 1:
        parser.error("--interval must be a positive integer (minimum: 1)")
    run_monitor(interval=args.interval)
