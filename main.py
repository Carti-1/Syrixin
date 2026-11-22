import time
import os
import datetime
import argparse

from monitor.battery import battery_status
from models.system_info import SystemInfo
from utils.formatter import (
    format_cpu,
    format_ram,
    format_disk,
    format_battery,
    format_history,
    display,
)
from logs.logger import log_info, log_warning, log_error
from storage.database import Database
from services.monitoring import collect_metrics



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


def show_history(limit: int = 10) -> None:
    """Print the most recent saved metric records and close the database."""
    database = Database("syrixin.db")
    try:
        rows = database.get_recent(limit)
        print(format_history(rows))
    finally:
        database.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Syrixin system monitor")
    parser.add_argument(
        "--interval", type=int, default=5,
        help="Refresh interval in seconds (default: 5, minimum: 1)"
    )
    parser.add_argument(
        "--history",
        nargs="?",
        const=10,
        type=int,
        metavar="N",
        help="Show the latest N saved metric records (default: 10)",
    )
    args = parser.parse_args()
    if args.interval < 1:
        parser.error("--interval must be a positive integer (minimum: 1)")
    if args.history is not None:
        if args.history < 1:
            parser.error("--history must be a positive integer (minimum: 1)")
        show_history(limit=args.history)
    else:
        run_monitor(interval=args.interval)
