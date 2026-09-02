# Node.js

Node.js 20 or later is required. This implementation uses the built-in Fetch
API and has no package dependencies.

```bash
cp .env.example .env
node --env-file=.env archive-job-execution-outputs.mjs
```

The script exits with status 0 on success, 1 for a fatal error, or 2 when one
or more selected executions could not be archived.
