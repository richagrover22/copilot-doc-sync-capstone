# Task Manager

A single-user task manager built with Flask and SQLite. Tasks can be created, edited, deleted, assigned a status and priority, and filtered by status and priority.

## Requirements

- Python 3.10 or newer

## Setup

From this directory, create and activate a virtual environment, then install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run

```powershell
python -m flask --app app run --host 127.0.0.1
```

The development server binds to loopback and debug mode is disabled by default. The SQLite database is created at `instance/tasks.db`.

Set `TASK_MANAGER_SECRET_KEY` to a private, stable value if sessions must remain valid across app restarts. Do not commit that value.

## Test

```powershell
python -m pytest -q
```

Tests use isolated temporary SQLite databases.
