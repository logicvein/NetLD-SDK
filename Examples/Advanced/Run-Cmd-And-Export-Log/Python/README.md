# Python implementation

```shell
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
cp .env.example .env
cp commands.txt.example commands.txt
python3 run_cmd_and_export_log.py
```

Set `NETLD_RUN_JOB=true` only after reviewing the preview. Run tests with:

```shell
python3 -m unittest discover -s tests -v
```

