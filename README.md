# Syrixin

Syrixin is a lightweight system monitor that helps you check how your computer is using its resources. It displays CPU, memory, disk, and battery information in your terminal and warns you when usage reaches high levels.

## What you can monitor

- **CPU:** current processor usage.
- **Memory:** percentage in use and total memory.
- **Disk:** used and total space for the monitored drive.
- **Battery:** charge level and whether the computer is plugged in, when battery information is available.

Syrixin checks these values repeatedly and refreshes the terminal display. It writes alerts and application events to `logs/syrixin.log` and saves each monitoring snapshot to a local SQLite database named `syrixin.db`. The database is created in the directory where you start the program; following the commands below creates it in the project folder. Missing or unavailable metrics are stored as `NULL` (no value). The database file is excluded from Git by default.

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

```bash
python main.py
```

By default, Syrixin waits five seconds after each monitoring cycle before checking again. To use a different wait time, pass the number of seconds with `--interval`:

```bash
python main.py --interval 10
```

Press **Ctrl+C** to stop monitoring.

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

Syrixin currently provides live monitoring, alerts, and a local history of collected measurements. It does not yet include a built-in way to browse or chart that history, AI analysis, or automatic optimization.

## Planned features

The project may grow to include:

- Tools to browse past measurements and spot trends.
- AI-assisted explanations and recommendations based on the collected data.
- Specific optimization actions, explained to the user and performed only with their approval.

These are future ideas, not features available in the current version. Their scope and order may change as the project develops.

## License

Syrixin is available under the MIT License. See [LICENSE](LICENSE) for details.
