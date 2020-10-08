## Terminal Proxy

The Terminal Proxy API provides the core functionality for auto-login to devices as well as
access to terminal proxy session histories.

#### One-time Authentication Token

Before a terminal proxy session to a device can proceed through the server, a one-time use
authentication token must be created. The authentication token can be created by calling the
``createTemporaryAuthenticationToken`` method on the Security service.

#### Security.createTemporaryAuthenticationToken
Creates a one-time use authentication token.

##### Parameters
| Parameter      | Type           | Description       |
| -------------- | -------------  | ----------------- |
| attributes     | JSON Object    | A JSON "map" that contains required attributes documented below |

The ``attributes`` parameter is a JSON map containing two key/value pairs:

| Key             | Value                                |
| --------------- | ------------------------------------ |
| targetDevice    | the IP address of the target device  |
| targetProtocol  | either "SSH" or "Telnet"             |

Example of the ``attributes`` map as expressed in JSON:
```json
{
   "targetDevice": "10.0.0.1",
   "targetProtocol": "SSH"
}
```

##### Return: An authentication one-time use token as a string.

Python example:

```python
from jsonrpc import JsonRpcProxy, JsonError

# netldHost should be defined as a variable containing the IP address/hostname of the NetLD server
netld_svc = JsonRpcProxy.fromHost(netldHost, "admin", "password")

attributes = {
   "targetDevice": "10.0.0.1",
   "targetProtocol": "SSH"
}

token = netld_svc.call('Security.createTemporaryAuthenticationToken', attributes)

print "Token: " + token
```

Note: The authentication token expires 30 seconds after creation, and therefore must be used
within that time.

<p class="vspacer"></p>

#### Complete Flow

Once an authentication token is obtained, you are free to initiate an SSH connection to the
server. Note that SSH is used to communitcate with the server regardless of the protocol (SSH or Telnet)
used to connect to the target device.

CLI Example:
```
ssh <token>@<netldHost>:2222
```
Where ``<token>`` is the token obtained via the API above, and ``<netldHost>`` is the IP address
or hostname of the server.

Some SSH clients, notably OpenSSH, accept the connection information in the form of a URI:
```
ssh ssh://<token>@<netldHost>:2222
```

When the session connects, if the user who created the token ("admin" in the example above) is
authorized to "auto-login" to the device then the server will guide the login process through the
auto-login procedure and leave the session connected at the target device command prompt immediately
following the login procedure.

<p class="vspacer"></p>

### Terminal Proxy Log Search and Retrieval

The ``TermLogs`` service provides search capability over the collection of terminal proxy logs
stored in the system.

#### TermLogs.search

Search supports many criteria, and the criteria can be combined to perform powerful searches.

| Parameter     | Type          | Description      |
| ------------- | ------------- | --------------   |
| scheme        | String        | A single scheme name, or comma-separated list of scheme names (see table below) |
| query         | String        | The query associated with the scheme(s) specified.  If there are multiple schemes specified, the query parameter should contain new-line (\n) characters between each query string |
| sortColumn    | String        | A string indicating the ``Device`` object attribute the results should be sorted by |
| descending    | Boolean       | A boolean flag indicating whether results should be sorted in descending or ascending order |

The ``scheme`` parameter is a single value, or a comma separated list of search schemes from the following table:

| Scheme             | Description     |
| ------------------ | --------------- |
| user               | The username of a specific user for which to find logs, can include leading or trailing wildcards |
| session            | A time value in which the log occurred. '24h', '7d', '30d', or a date range e.g. '2020-01-00T00:00:00/2020-05-15T08:15:30' |
| since              | A start time value in the format of '2020-05-15T08:15:30' |
| network            | A single value, or CSV of network names in which target devices must reside |
| target             | The specific IP address of the device that was the target of the session |
| client             | The specific IP address of the client that was the source of the session |
| hostname           | The hostname of the device that was the target of the session, can include leading or trailing wildcards |
| text               | Specific text that must appear within the terminal log |

The ``query`` parameter defines the query criteria to be used and is in association with the schemes defined by the ``scheme`` parameter.
For example, if you wish to search based on scheme ``user`` and ``hostname`` you would specify a ``scheme`` parameter of "user,hostname", and
a ``query`` parameter of "william\ntokyo*".  Note the newline character between the ``user`` query value and the ``hostname`` query value.

#### Return: An array of ``TermLogSearchResult`` objects

### Terminal Proxy Objects

#### TermLogSearchResult

| Field           | Type          | Description      |
| --------------- | ------------- | --------------   |
| logId           | Integer       | The internal log identifier. |
| username        | String        | The username of the user who connected to the device. |
| sessionStart    | Date          | The start time of the terminal session. |
| sessionEnd      | Date          | The end time of the terminal session. |
| ipAddress       | String        | The IPv4 or IPv6 address of the device. |
| clientIpAddress | String        | The IPv4 or IPv6 address of the client computer. |
| hostname        | String        | The hostname of the device. |
| managedNetwork  | String        | The name of the managed network that the device resides in. |
| protocol        | String        | The protocol used between the server and target device. |

<p class="vspacer"></p>

### Individual Terminal Log Retrieval

Once a ``TermLogSearchResult`` record of a terminal proxy log has been obtained via search, the content of a
desired terminal log can be retrieved via a simple HTTP ``GET`` request.

Required HTTP URL parameters:

| Field           | Value     |
| --------------- | --------- |
| op              | "content", constant string |
| stripXml        | "true", constant string |
| sessionStart    | The ``sessionStart`` value from a ``TermLogSearchResult`` record |
| ipAddress       | The ``ipAddress`` value from a ``TermLogSearchResult`` record |
| managedNetwork  | The ``managedNetwork`` value from a ``TermLogSearchResult`` record |

A Python example, in continuation of the example above (some URL parameters omitted for brevity):
```python
import urllib2
...

opener = urllib2.build_opener(netld_svc._cookie_processor, netld_svc._https_handler)
url = 'https://{0}/servlet/termlog?op=content&stripXml=true&sessionStart={1}...'.format(netld_svc._host, record['sessionStart'], ...)
resp = opener.open(url)
respdata = str(resp.read())
```
