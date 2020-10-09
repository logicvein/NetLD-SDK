## Jumphosts

The ``Jumphost`` service allows configuration of jumphost parameters on specific networks.

### Methods

#### Jumphost.getJumphostForNetwork
Get the jumphost configuration for a specified network, if it exists.

##### Parameters
| Parameter      | Type   | Description      |
| -------------- | ------ | --------------   |
| networkName | String | The network name |

##### Return: a hashmap (key/value pairs) of jumphost settings, or null if none exist for the specified network

Python example:
```python
from jsonrpc import JsonRpcProxy, JsonError

# netldHost should be defined as a variable containing the IP address/hostname of the NetLD server
netld_svc = JsonRpcProxy.fromHost(netldHost, "admin", "password")

network = "Default"

properties = netld_svc.call('Jumphost.getJumphostForNetwork', network)

for key in properties.keys():
   print key + ": " + properties[key]

netld_svc.call('Security.logoutCurrentUser')
```

*Note: The ``jsonrpc`` functions are defined in ``jsonrpc.py`` in the SDK ``Examples/Python`` folder. Simply include that file in the same directory as your script.*

#### Jumphost.saveJumphost
Create/update jumphost setting for a specified network. Ideally, when *updating* jumphost settings for a specific network
it is recommended to first retrieve the properties via ``Jumphost.getJumphostForNetwork``, modify them, and then use this
method to save them. This ensures that any *internal use* properties that exists are not overwritten.

##### Parameters
| Parameter      | Type   | Description      |
| -------------- | ------ | --------------   |
| networkName    | String | The network name |
| properties     | Map    | A JSON map of key/value pairs, as documented below |

##### Return: void

The following are the required *keys* that must be present in the ``properties`` parameter:

| Field           | Value     | Description |
| --------------- | --------- | ----------- |
| enabled         | ``"true"``/``"false"`` | whether the jumphost is enabled or not |
| host            | IP address/hostname | The IP address/hostname of the jumphost |
| username        | String    | the username required to login to the jumphost |
| password        | String    | the password required to login to the jumphost |
| adapter         | String    | must be either ``"Cisco::IOS"`` or ``"Linux::Redhat"`` |

Python example:
```python
from jsonrpc import JsonRpcProxy, JsonError

# netldHost should be defined as a variable containing the IP address/hostname of the NetLD server
netld_svc = JsonRpcProxy.fromHost(netldHost, "admin", "password")

network = "Default"

properties = {
   "enabled": "true",
   "host": "10.0.0.1",
   "username": "jsmith",
   "password": "mysecret",
   "adapter": "Linux::Redhat"
}

netld_svc.call('Jumphost.saveJumphost', network, properties)

netld_svc.call('Security.logoutCurrentUser')
```
*Note: The ``jsonrpc`` functions are defined in ``jsonrpc.py`` in the SDK ``Examples/Python`` folder. Simply include that file in the same directory as your script.*
