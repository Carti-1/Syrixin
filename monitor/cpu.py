import psutil


def _get_temperature_from_lhm():
    from services.hardware import get_hardware_inventory

    for component in get_hardware_inventory():
        component_name = component["name"].lower()
        for sensor in component["sensors"]:
            sensor_name = sensor["name"].lower()
            cpu_sensor = (
                "cpu" in component_name
                or "processor" in component_name
                or any(token in sensor_name for token in ("cpu", "tctl", "tdie"))
            )
            if sensor["type"].lower() == "temperature" and cpu_sensor:
                value = sensor["value"]
                if isinstance(value, (int, float)):
                    return float(value)
    return None


def _get_temperature_from_legacy_wmi():
    """Support older LibreHardwareMonitor versions that still expose WMI."""
    import wmi

    monitor = wmi.WMI(namespace="root\\LibreHardwareMonitor")
    for sensor in monitor.Sensor():
        name = sensor.Name or ""
        value = sensor.Value
        if sensor.SensorType == "Temperature" and "cpu" in name.lower() and value is not None:
            return float(value)
    return None

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

    # Current LibreHardwareMonitor versions expose their sensors over localhost.
    try:
        temperature = _get_temperature_from_lhm()
        if temperature is not None:
            return temperature
    except Exception:
        # Older LHM versions used WMI instead of the current HTTP endpoint.
        pass

    try:
        return _get_temperature_from_legacy_wmi()
    except Exception:
        # Missing tool, missing endpoint, or unavailable sensor is normal.
        pass
    return None

def get_cpu_use(interval=1):
    cpu = psutil.cpu_percent(interval=interval)
    return cpu
