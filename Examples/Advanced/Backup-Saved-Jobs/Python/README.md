# Python

Requires Python 3.10 or later.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 backup_saved_jobs.py
```

For repository testing, use `python3 backup_saved_jobs.py --env ../../../.env.netld`.
Run tests with `python3 -m unittest discover -s tests`.
