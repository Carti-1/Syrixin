# Syrixin

Syrixin is a lightweight system monitor that helps you check how your computer is using its resources. It offers a desktop window with live metric cards and a CPU usage chart, as well as a terminal mode and alerts.

## What you can monitor

- **CPU:** current processor usage.
- **CPU temperature:** current temperature when the computer exposes a supported sensor.
- **Memory:** total capacity, percentage in use, and estimated physical memory in use.
- **Disk:** used and total space for the monitored drive.
- **Battery:** charge level and whether the computer is plugged in, when battery information is available.

Syrixin checks these values repeatedly and refreshes the display. It writes alerts and application events to `logs/syrixin.log` and saves each monitoring snapshot to a local SQLite database named `syrixin.db`. The database is created in the directory where you start the program; following the commands below creates it in the project folder. Missing or unavailable metrics are stored as `NULL` (no value). The database file is excluded from Git by default.

On Windows, CPU temperature and the Hardware tab can use [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor), which must be running with **Options → Remote Web Server → Run** enabled. Syrixin reads its local endpoint at `127.0.0.1:8085/data.json`; if the endpoint or a sensor is unavailable, the rest of monitoring continues.

LibreHardwareMonitor is a separate Windows application, not a Python package, so it is not installed by `requirements.txt`. Users who need these readings must download and start it separately.

## Requirements

- Python 3.10 or newer
- An internet connection for the initial installation

## Install

Open a terminal and run:

```bash
git clone https://github.com/Carti-1/Syrixin.git
cd Syrixin
python -m pip install -r requirements.txt
```

## Start monitoring

To open the desktop window:

```bash
python -m ui.app
```

The desktop cards refresh about once per second. The CPU card includes a compact graph of recent usage, while the memory, disk, and battery cards use visual indicators that reflect their current readings. To keep the local database from growing too quickly, snapshots are saved every five seconds. The **Hardware** tab lists components and sensor readings exposed by LibreHardwareMonitor. The **Logs** tab shows recent application events, and **Assistente IA** outlines planned capabilities; AI features are not connected yet.

To use the terminal monitor instead:

```bash
python main.py
```

By default, Syrixin waits five seconds after each monitoring cycle before checking again. To use a different wait time, pass the number of seconds with `--interval`:

```bash
python main.py --interval 10
```

Press **Ctrl+C** to stop monitoring.

## View recent history

After Syrixin has saved some monitoring snapshots, you can view the ten most recent records with:

```bash
python main.py --history
```

To choose how many records to display, pass a positive number:

```bash
python main.py --history 25
```

The history includes the timestamp and available CPU, CPU temperature, memory, disk, and battery measurements. Unavailable values appear as `N/A`.

## Alerts

The current default alerts are:

| Resource | Alert condition |
|---|---|
| CPU | Usage is above 90% |
| Memory | Usage is above 85% |
| Disk | Usage is above 90% |
| Battery | Charge is below 20% while unplugged |

Alert thresholds are currently built into the program and cannot yet be changed from the command line. A computer without a battery may show that battery data is unavailable; CPU, memory, and disk monitoring continue independently.

## Current scope

Syrixin currently provides live desktop and terminal monitoring, alerts, a CPU usage chart, and a command-line view of locally saved measurements. It does not yet include AI analysis or automatic optimization.

## Planned features

The project may grow to include:

- AI-assisted explanations and recommendations based on the collected data.
- Specific optimization actions, explained to the user and performed only with their approval.

These are future ideas, not features available in the current version. Their scope and order may change as the project develops.

## License

Syrixin is available under the MIT License. See [LICENSE](LICENSE) for details.
