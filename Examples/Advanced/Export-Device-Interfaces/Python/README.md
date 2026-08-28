# Python

Requires Python 3.10 or later.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 export_device_interfaces.py
```

For repository testing, use the shared environment file without copying it:

```sh
python3 export_device_interfaces.py --env ../../../.env.netld
```

Run tests with `python3 -m unittest discover -s tests`.
