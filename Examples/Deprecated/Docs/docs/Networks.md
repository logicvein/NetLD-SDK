## Networks
The networks API provides the functionality for managing the managed network definitions.

See the [Objects](#objects) section for a description of the various objects consumed and returned by these APIs.

### Methods

#### Networks.defineManagedNetwork
Create a new Managed Network within the system.
##### Parameters
| Parameter      | Type   | Description      |
| -------------- | ------ | --------------   |
| networkName | String | The network name |
| bridgeName | String | The name of the smart bridge |

##### Return: void

#### Networks.getManagedNetwork
Get the Managed Network identified by name.
##### Parameters
| Parameter      | Type   | Description      |
| -------------- | ------ | --------------   |
| networkName | String | The network name |

##### Return: A [ManagedNetwork](#managednetwork) object


#### Networks.getManagedNetworkNames
Get the names of the Managed Networks that have been defined.
##### Parameters
None

##### Return: An array of Strings

#### Networks.getAllManagedNetworks
Get a list of all Managed Networks that have been defined.
##### Parameters
None

##### Return: An array of [ManagedNetwork](#managednetwork) objects

#### Networks.deleteManagedNetwork
Delete a Managed Network identified by the name.
##### Parameters
| Parameter      | Type   | Description      |
| -------------- | ------ | --------------   |
| networkName | String | The network name |
##### Return: void

#### Networks.updateManagedNetwork
Update a Managed Network's information using the contents of the supplied ManagedNetwork
instance.  This instance must encapsulate information about a Managed Network that actually
exists, otherwise an exception is thrown.

##### Parameters
| Parameter      | Type   | Description      |
| -------------- | ------ | --------------   |
| network | [ManagedNetwork](#managednetwork) | The network to update |

##### Return: void

#### Networks.getManagedNetworksByBridge
Get all managed networks by bridge.

##### Parameters
| Parameter      | Type   | Description      |
| -------------- | ------ | --------------   |
| bridgeName | String | The smart bridge name |

##### Return: An array of [ManagedNetwork](#ManagedNetwork) objects

### Objects
#### ManagedNetwork
| Attribute | Type | Description |
| --------- | ---- | ----------- |
| name | String | The managed network name |
| bridgeName | String | The name of the associated smart bridge |
| online | Boolean | The current online state of the bridge |
