# Python

Requires Python 3.10 or later. Install `requirements.txt`, copy `.env.example`
to `.env`, and run `python3 archive_configuration_revisions.py`.

For repository testing, use:

```sh
python3 archive_configuration_revisions.py --env ../../../.env.netld
```

Run tests with `python3 -m unittest discover -s tests`.
