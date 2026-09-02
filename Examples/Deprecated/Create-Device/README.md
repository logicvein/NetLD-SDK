# Deprecated Create-Device Examples

These implementations are retained only for historical inspection. They have been superseded by the maintained, tested [Create a Device](../../Getting-Started/Create-Device/) example for Python, PowerShell, and Node.js.

The historical scripts all perform the same demonstration cycle: create a hard-coded Cisco IOS device at `10.10.10.10`, retrieve it, and immediately delete it. They add no create-device behavior that is absent from the maintained example.

Do not run these scripts against a production system. Depending on the language, they contain hard-coded credentials, put credentials in request URLs, disable TLS certificate verification, use obsolete positional API calls, and delete the target record without an explicit confirmation or preview step.

The older Python 2 variant remains in [`Deprecated/Python-2`](../Python-2/createDevice.py) with the rest of its shared Python 2 runtime.

