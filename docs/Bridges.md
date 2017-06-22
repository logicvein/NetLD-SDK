## Bridges

The bridges API provides the functionality of managing the smart bridge settings.


### Objects
#### Bridge
| Attribute | Type | Description |
| bridgeId | Integer | The database ID of the bridge |
| name | String | The SmartBridge name |
| hostOrIp | String | The host or IP address of the smart bridge |
| port | Integer | The port to connect to the smart bridge on. |
| inbound | Boolean | True if the smart bridge initiates the connection to the core server, false if the core server initiates the connection to the smart bridge. |
| token | String | The authentication token used for connecting to the smart bridge. |

### Methods 
#### Bridges.defineBridge
Create a new network bridge within the system.

##### Parameters
| Parameter      | Type          | Description      |
| -------------- | ------------- | --------------   |
| bridgeName     | String | The SmartBridge name |
| hostOrIp       | String | The host or IP address of the smart bridge |
| port      | String   | The port to connect to the smart bridge on. |
| inbound | Boolean | True if the smart bridge initiates the connection to the core server, false if the core server initiates the connection to the smart bridge. |
| token | String | The authentication token used for connecting to the smart bridge. |

##### Return: void

#### Bridges.getBridge
Get a bridge by name.
##### Parameters
| Parameter      | Type          | Description      |
| -------------- | ------------- | --------------   |
| bridgeName | String | The SmartBridge name |

##### Return: A `Bridge` object

#### Bridges.getAllBridges
Get all of the defined bridges.

##### Parameters
None

##### Return: An array of `Bridge` objects

#### Bridges.deleteBridge
Delete the bridge definition with the specified name
##### Parameters
| Parameter      | Type          | Description      |
| -------------- | ------------- | --------------   |
| bridgeName | String | The SmartBridge name |

##### Return: void

#### Bridges.updateBridge
Get a bridge by name.
##### Parameters
| Parameter      | Type          | Description      |
| -------------- | ------------- | --------------   |
| bridge | Bridge | The bridge definition to update |

##### Return: void
