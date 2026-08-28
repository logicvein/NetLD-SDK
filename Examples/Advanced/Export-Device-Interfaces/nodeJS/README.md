# Node.js

Requires Node.js 20 or later and has no third-party dependencies.

```sh
cp .env.example .env
node export-device-interfaces.mjs
```

For repository testing, use the shared environment file without copying it:

```sh
node export-device-interfaces.mjs --env ../../../.env.netld
```

Run tests with `npm test`.
