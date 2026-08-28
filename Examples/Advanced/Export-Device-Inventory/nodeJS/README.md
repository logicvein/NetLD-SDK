# Node.js

Requires Node.js 20 or later. This example has no third-party runtime
dependencies.

```sh
cp .env.example .env
node export-device-inventory.mjs
```

Edit `.env` before running the script. `NETLD_NETWORKS` accepts a comma-separated
list such as `Default,Lab`. The completed output replaces the destination only after
every page has been retrieved successfully.

Use JSON or the shared repository test environment with:

```sh
node export-device-inventory.mjs --format json --env ../../../.env.netld
```

Run the unit tests with:

```sh
node --test
```
