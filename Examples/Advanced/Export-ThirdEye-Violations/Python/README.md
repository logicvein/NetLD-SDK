# Python

Requires Python 3.10 or newer.

From this directory, create or activate a virtual environment and install the
two runtime dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env`, set the ThirdEye URL and API key, and run:

```bash
python export_thirdeye_violations.py
```

To keep credentials in another location:

```bash
python export_thirdeye_violations.py --env /path/to/.env
```

See the [parent README](../README.md) for configuration, output, state, and API
compatibility details.
