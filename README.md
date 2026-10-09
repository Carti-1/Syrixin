# Syrixin — Intelligent System Monitor

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Syrixin is a lightweight Python system monitor that tracks CPU, RAM, disk, and battery usage in real time. It logs metrics automatically and raises configurable alerts when resources exceed defined thresholds.

---

## Features

- Real-time CPU usage monitoring
- RAM usage monitoring
- Disk space monitoring
- Battery level and charging status monitoring
- Automatic logging with timestamps
- Configurable alert thresholds
- Modular architecture (each metric is an independent module)

---

## Requirements

- Python 3.10+
- [psutil](https://pypi.org/project/psutil/)

---

## Installation

```bash
git clone https://github.com/your-username/syrixin.git
cd syrixin
pip install -r requirements.txt
```

---

## Usage

```bash
python main.py
```

Sample output:

```
CPU: 12.5%
RAM: 7.82 GB / 48.8%
Disk: 142.31 GB / 476.84 GB (29.9%)
Battery: 87% / Charging
```

---

## Running Tests

```bash
python -m unittest discover -s tests -v
```

---

## Project Structure

```
Syrixin/
├── main.py               # Entry point and alert logic
├── monitor/
│   ├── cpu.py            # CPU data collection
│   ├── memory.py         # RAM data collection
│   ├── disk.py           # Disk data collection
│   └── battery.py        # Battery data collection
├── models/
│   └── system_info.py    # System data model
├── utils/
│   └── formatter.py      # Output formatting
├── tests/
│   ├── test_cpu.py
│   ├── test_memory.py
│   ├── test_disk.py
│   ├── test_battery.py
│   ├── test_formatter.py
│   ├── test_system_info.py
│   ├── test_alerts.py
│   └── test_failures.py
└── logs/
    ├── logger.py         # Logging configuration
    └── syrixin.log       # Generated log file
```

---

## Alert Thresholds

| Metric  | Threshold        | Condition                          |
|---------|------------------|------------------------------------|
| CPU     | > 90%            | Usage exceeds 90%                  |
| RAM     | > 85%            | Usage exceeds 85%                  |
| Disk    | > 90%            | Disk usage exceeds 90%             |
| Battery | < 20% unplugged  | Battery below 20% and not charging |
| Battery | absent           | No battery detected (desktop)      |

---

## License

MIT License — see [LICENSE](LICENSE) for details.
