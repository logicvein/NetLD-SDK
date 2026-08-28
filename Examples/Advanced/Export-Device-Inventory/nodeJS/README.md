# Node.js

Requires Node.js 20 or later. This example has no third-party runtime
dependencies.

```sh
cp .env.example .env
node export-device-inventory.mjs
```

Edit `.env` before running the script. `NETLD_NETWORKS` accepts a comma-separated
list such as `Default,Lab`. The completed CSV replaces the destination only after
every page has been retrieved successfully.

Run the unit tests with:

```sh
npm test
```
