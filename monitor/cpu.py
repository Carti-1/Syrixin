import psutil

def get_cpu_temperature():
    """Return a CPU temperature in Celsius, or None when unavailable.

    psutil exposes hardware temperatures only on supported OS/hardware.
    Select CPU-related sensors so disk and other temperatures aren't confused
    with CPU temperature.
    """
    get_sensors = getattr(psutil, "sensors_temperatures", None)
    if get_sensors is not None:
        try:
            sensors = get_sensors()
            for name, entries in sensors.items():
                if not any(token in name.lower() for token in ("cpu", "coretemp", "k10temp", "soc")):
                    continue
                for entry in entries:
                    if entry.current is not None:
                        return float(entry.current)
        except (NotImplementedError, OSError):
            # Windows and some hardware need a separate sensor provider.
            pass

    # Optional Windows integration: requires LibreHardwareMonitor running with
    # its WMI support enabled, plus the small `wmi` Python package.
    try:
        import wmi

        monitor = wmi.WMI(namespace="root\\LibreHardwareMonitor")
        for sensor in monitor.Sensor():
            name = sensor.Name or ""
            if sensor.SensorType == "Temperature" and "cpu" in name.lower():
                value = sensor.Value
                if value is not None:
                    return float(value)
    except Exception:
        # Missing tool, missing WMI namespace, or unavailable sensor is normal.
        return None
    return None

def get_cpu_use(interval=1):
    cpu = psutil.cpu_percent(interval=interval)
    return cpu
