# Node.js

## Prerequisites

- Node.js 20 or later
- Network access, API tokens, certificates, and a discovery job as described in
  the [integration README](../README.md)

From this directory:

```bash
npm install
cp .env.example .env
```

Edit `.env` with the values for your environment.

Preview missing devices without starting discovery:

```bash
node live-nx-to-thirdeye.mjs
```

After reviewing the preview, start discovery with:

```bash
node live-nx-to-thirdeye.mjs --apply
```

Run the offline tests with:

```bash
npm test
```
