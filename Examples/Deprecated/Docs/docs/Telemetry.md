## Telemetry

The telemetry API provides the core functionality of retrieving device neighbor information from the inventory.

See the [Telemetry Objects](#telemetry-objects) section for a description of the various objects consumed and returned by these APIs.

#### Telemetry.getArpTable
Retrieves an entire ARP table for the given device.

##### Parameters
| Parameter      | Type          | Description      |
| -------------- | ------------- | --------------   |
| pageData       | JSON Object    | A ```PageData``` object specifying the starting ```offset``` and ```pageSize```. |
| managedNetwork | String   | Name of an existing network, e.g. "Default" |
| ipAddress      | String   | IPv4 or IPv6 address |
| sort           | String   | A string indicating the `ArpTableEntry` object attribute the results should be sorted by, *null* for default |
| descending     | Boolean  | A boolean flag indicating whether results should be sorted in descending or ascending order. |

##### Return: A `ArpPageData` object of the last retreived ARP table.

#### Telemetry.getArpEntries
Retrieves all ARP entries from all devices where the IP Address of the ARP entry is contained in the provided networkAddress.

##### Parameters
| Parameter      | Type          | Description      |
| -------------- | ------------- | --------------   |
| pageData       | JSON Object    | A ```PageData``` object specifying the starting ```offset``` and ```pageSize```. |
| networkAddress | String | The address to get entries on, e.g. '10.100.0.0/16'
| sort           | String | A string indicating the `DeviceArpTableEntry` object attribute the results should be sorted by, *null* for default |
| descending     | Boolean  | A boolean flag indicating whether results should be sorted in descending or ascending order. |
| networks       | Array | An array of managed network names to search |

##### Return: A `DeviceArpPageData` object.

#### Telemetry.getMacTable
Retrieves an entire MAC forwarding table for the given device.

##### Parameters
| Parameter      | Type          | Description      |
| -------------- | ------------- | --------------   |
| pageData       | JSON Object    | A ```PageData``` object specifying the starting ```offset``` and ```pageSize```. |
| managedNetwork | String   | Name of an existing network, e.g. "Default" |
| ipAddress      | String   | IPv4 or IPv6 address |
| sort           | String   | A string indicating the `MacTableEntry` object attribute the results should be sorted by, *null* for default |
| descending     | Boolean  | A boolean flag indicating whether results should be sorted in descending or ascending order. |

##### Return: A `MacPageData` object.

#### Telemetry.getNeighbors
Retrieves routing (OSPF, EIGRP, BGP) and discovery protocol neighbors (CDP, NDP) for the given device.

##### Parameters
| Parameter      | Type   | Description      |
| -------------- | ------ | --------------   |
| managedNetwork | String | Name of an existing network, e.g. "Default" |
| ipAddress      | String | IPv4 or IPv6 address |

##### Returns: An Array of `Neighbor` objects.

#### Telemetry.findSwitchPort
Given a host IP, MAC address or hostname, find the switch port that the device is physically plugged into.

##### Parameters
| Parameter      | Type   | Description      |
| -------------- | ------ | --------------   |
| host | String | the host as a MAC address, and IP address or a hostname
| networks | Array | An array of managed network names to search |

##### Return: A `SwitchPortResult` object.

### Telemetry Objects
#### ArpPageData
| Attribute     | Type          | Description      |
| ------------- | ------------- | --------------   |
| offset        | Integer       | The starting ```offset``` in the results to begin retrieving ```pageSize``` number of ```ArpTableEntry``` objects.  This value is required when ```ArpPageData``` is used as a parameter. |
| pageSize      | Integer       | The maximum number of ```ArpTableEntry``` objects to retrieve in a single method call. This value is required when ```ArpPageData``` is used as a parameter. |
| total         | Integer  | This value is set and retrieved from the server when an ```offset``` of zero (0) is passed.  This indicates the total number of ``ArpTableEntry`` objects available.   This value is ignored when ```ArpPageData``` is used as a parameter. |
| arpEntries    | Array | An array of ``ArpTableEntry`` objects. This value is ignored when ``ArpPageData`` is used as a parameter. |

#### ArpTableEntry
| Attribute     | Type          | Description      |
| ------------- | ------------- | --------------   |
| ipAddress | String | The IP Address |
| interfaceName | String | The interface name |
| macAddress | String | The MAC address |

#### DeviceArpPageData
| Attribute     | Type          | Description      |
| ------------- | ------------- | --------------   |
| offset        | Integer       | The starting ```offset``` in the results to begin retrieving ```pageSize``` number of ```DeviceArpTableEntry``` objects.  This value is required when ```DeviceArpPageData``` is used as a parameter. |
| pageSize      | Integer       | The maximum number of ```DeviceArpTableEntry``` objects to retrieve in a single method call. This value is required when ```DeviceArpPageData``` is used as a parameter. |
| total         | Integer  | This value is set and retrieved from the server when an ```offset``` of zero (0) is passed.  This indicates the total number of ``DeviceArpTableEntry`` objects available.   This value is ignored when ```DeviceArpPageData``` is used as a parameter. |
| arpEntries    | Array | An array of ``DeviceArpTableEntry`` objects. This value is ignored when ``DeviceArpPageData`` is used as a parameter. |

#### DeviceArpTableEntry
| Attribute     | Type          | Description      |
| ------------- | ------------- | --------------   |
| device | String | The IP Address of the device that the ARP entry was found on. |
| managedNetwork | String | The managed network of the device that the ARP entry was found on. |
| ipAddress | String | The IP Address in the ARP entry. |
| macAddress | String | The MAC Address in the ARP entry. |
| interfaceName | String | The interface name in the ARP entry. |

#### MacPageData
| Attribute     | Type          | Description      |
| ------------- | ------------- | --------------   |
| offset        | Integer       | The starting ```offset``` in the results to begin retrieving ```pageSize``` number of ```MacTableEntry``` objects.  This value is required when ```MacPageData``` is used as a parameter. |
| pageSize      | Integer       | The maximum number of ```MacTableEntry``` objects to retrieve in a single method call. This value is required when ```MacPageData``` is used as a parameter. |
| total         | Integer  | This value is set and retrieved from the server when an ```offset``` of zero (0) is passed.  This indicates the total number of ``MacTableEntry`` objects available.   This value is ignored when ```MacPageData``` is used as a parameter. |
| macEntries    | Array | An array of ``MacTableEntry`` objects. This value is ignored when ``MacPageData`` is used as a parameter. |

#### MacTableEntry
| Attribute     | Type          | Description      |
| ------------- | ------------- | --------------   |
| port | String | The port in the MAC table. |
| vlan | String | The VLAN in the MAC table. |
| macAddress | String | The MAC Address in the MAC table. |

#### Neighbor
| Attribute     | Type          | Description      |
| ------------- | ------------- | --------------   |
| protocol | String | The neighbor protocol (OSPF, BGP, CDP, etc) |
| ipAddress | String | The IP Address of the neighbor |
| localInterface | String | The local interface that the neighbor was seen on. |
| remoteInterface | String | The interface on the neighbor |
| otherId | String | The neighbors 'ID' |

#### SwitchPortResult
| Attribute     | Type          | Description      |
| ------------- | ------------- | --------------   |
| hostIpAddress | String | The target IP Address |
| hostMacAddress | String | The MAC address of the host |
| arpEntry | DeviceArpTableEntry | The ARP entry that the host was found on. |
| macEntry | DeviceMacTableEntry | The MAC table entry that the host was found on. |
| error | Integer | An error code. <ul><li>0 - no error</li><li>1 - unable to resolve host</li><li>2 - unable to find IP in an ARP/NDP table</li><li>3 - unable to find the MAC address in a forwarding table</li></ul> |
