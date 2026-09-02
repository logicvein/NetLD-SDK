# Deprecated Static-Credential Importer

The Python 3 files in this directory are retained solely for historical
inspection. Do not run the importer against a current netLD or ThirdEye system.

`staticCredentials.py` changes device-authentication credentials on the
appliance. It accepts the appliance username and password on the command line,
places them in the request URL, converts the source CSV into an unprotected
`credentials.xlsx` file, and uploads that workbook through the old
`/servlet/credentials` endpoint. It has no preview, confirmation, transactional
rollback, or protection against an authentication redirect being mistaken for
success. Its command-line options are also inconsistent and its Python
dependencies are not declared.

The accompanying `static-creds.csv` is an unpopulated format sample. Never put
real secrets into a tracked repository file.

There is no maintained replacement for this importer. The current
[Credentials API](https://docs.logicvein.com/manuals/logicvein-api/credentials/)
documents the structured `Credentials.saveCredentialSets` method and requires
the same session to finish with `Credentials.commitEdits` or
`Credentials.discardEdits`. Any future credential-import example should use
that transaction contract, keep preview as the default, avoid intermediate
plaintext files, and require an explicit commit option.
