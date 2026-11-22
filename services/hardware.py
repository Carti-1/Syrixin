"""Read local hardware names and sensors from LibreHardwareMonitor's HTTP API."""

import json
import re
from urllib.error import URLError
from urllib.request import urlopen


DEFAULT_HARDWARE_URL = "http://127.0.0.1:8085/data.json"
_NUMBER_PATTERN = re.compile(r"[-+]?(?:\d+(?:[.,]\d*)?|[.,]\d+)")


class HardwareMonitorUnavailable(RuntimeError):
    """Raised when LibreHardwareMonitor's local data endpoint cannot be read."""


def _parse_sensor_value(value):
    """Normalize numeric sensor values, including localized strings like 60,0 °C."""
    if isinstance(value, (int, float)):
        return value
    if not isinstance(value, str):
        return value

    match = _NUMBER_PATTERN.search(value)
    if match is None:
        return value

    number = match.group(0).replace(",", ".")
    try:
        return float(number)
    except ValueError:
        return value


def get_hardware_inventory(url=DEFAULT_HARDWARE_URL, timeout=0.5):
    """Return detected components and their sensor readings from local LHM."""
    try:
        with urlopen(url, timeout=timeout) as response:
            payload = json.load(response)
    except (URLError, TimeoutError, OSError) as error:
        raise HardwareMonitorUnavailable(
            "LibreHardwareMonitor is unavailable. Start it and enable "
            "Options > Remote Web Server > Run."
        ) from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise HardwareMonitorUnavailable(
            "LibreHardwareMonitor returned invalid sensor data."
        ) from error

    components = []
    seen_ids = set()

    def collect_sensor_nodes(node, sensors):
        for child in node.get("Children", []):
            # A nested hardware device is listed as its own component below.
            if child.get("HardwareId"):
                continue
            if child.get("SensorId"):
                value = child.get("RawValue")
                if value is None:
                    value = child.get("Value")
                sensors.append({
                    "name": child.get("Text", "Sensor"),
                    "type": child.get("Type", ""),
                    "value": _parse_sensor_value(value),
                })
            collect_sensor_nodes(child, sensors)

    def walk(node):
        hardware_id = node.get("HardwareId")
        if hardware_id and hardware_id not in seen_ids:
            seen_ids.add(hardware_id)
            component = {
                "name": node.get("Text", "Unknown component"),
                "identifier": hardware_id,
                "sensors": [],
            }
            collect_sensor_nodes(node, component["sensors"])
            components.append(component)

        for child in node.get("Children", []):
            walk(child)

    if isinstance(payload, dict):
        walk(payload)
    return sorted(components, key=lambda component: component["name"].casefold())
