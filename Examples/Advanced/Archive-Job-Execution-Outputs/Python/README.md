# Python

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 archive_job_execution_outputs.py
```

On Windows, activate the environment with
`.\.venv\Scripts\Activate.ps1`.

The script exits with status 0 on success, 1 for a fatal error, or 2 when one
or more selected executions could not be archived.
