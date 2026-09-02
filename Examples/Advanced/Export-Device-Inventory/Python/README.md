# Python

Requires Python 3.10 or later.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 export_device_inventory.py
```

Edit `.env` before running the script. `NETLD_NETWORKS` accepts a comma-separated
list such as `Default,Lab`. The completed output replaces the destination only after
every page has been retrieved successfully.

Use JSON or the shared repository test environment with:

```sh
python3 export_device_inventory.py --format json --env ../../../.env.netld
```

Run the unit tests with:

```sh
python3 -m unittest discover -s tests
```
