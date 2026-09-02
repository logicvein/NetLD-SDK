# Node.js

Requires Node.js 20 or newer and has no package dependencies.

Copy `.env.example` to `.env`, set the ThirdEye URL and API key, and run:

```bash
node export-thirdeye-violations.mjs
```

To keep credentials in another location:

```bash
node export-thirdeye-violations.mjs --env /path/to/.env
```

See the [parent README](../README.md) for configuration, output, state, and API
compatibility details.
