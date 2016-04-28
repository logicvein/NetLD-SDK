## Overview

The inventory API provides the core functionality of manipulating devices in the Net LineDancer inventory, including: adding devices, deleting devices, modifying devices, searching devices, etc.

Many of the inventory methods accept or return a "device object" (e.g. Device) which encapsulates the basic attributes of a device in Net LineDancer.  This ```Device``` is expressed in JSON format
as shown in the following example:

```javascript
{  
   "ipAddress": "10.0.3.6",
   "hostname": "C2611-2",
   "adapterId": "Cisco::IOS",
   "deviceType": "Router",
   "hardwareVendor": "Cisco",
   "model": "CISCO2611XM-2FE",
   "softwareVendor": "Cisco",
   "osVersion": "12.4(12)",
   "backupStatus": "SUCCESS",
   "complianceState": 0,
   "lastBackup": 1410324618367,
   "lastTelemetry": null,
   "memoSummary": null,
   "custom1": "",
   "custom2": "",
   "custom3": "",
   "custom4": "",
   "custom5": "",
   "network": "Default",
   "serialNumber": "JAE07170S8Q"
}
```

<p class="vspacer"></p>

The ```search``` API returns a ```PageData``` object, as well as accepting a ```PageData``` as a parameter is expressed in JSON format seen here:

```javascript
{
    "offset": 0,
    "pageSize": 10,
    "total": 27,
    "devices": [<Device> objects]
}
```

<p></p>

| Attribute     | Type          | Description      |
| ------------- | ------------- | --------------   |
| offset        | Integer       | The starting ```offset``` in the results to begin retrieving ```pageSize``` number of ```Device``` objects.  This value is required when ```PageData``` is used as a parameter. |
| pageSize      | Integer       | The maximum number of ```Device``` objects to retrieve in a single method call. This value is required when ```PageData``` is used as a parameter. |
| total         | Integer       | This value is set and retrieved from the server when an ```offset``` of zero (0) is passed.  This indicates the total number of ```Device``` objects available.   This value is ignored when ```PageData``` is used as a parameter. |
| devices       | Array         | An array of ```Device``` objects. This value is ignored when ```PageData``` is used as a parameter. |

<p class="vspacer"></p>

### ```Inventory.createDevice```
Add a device to the inventory, in the specified network.  If there are no user-defined networks then "Default" should be used as the ``network`` value.  If the device was created successfully, the return value is ```null```, otherwise an error
message is returned.

#### Parameters
| Parameter     | Type          | Description      |
| ------------- | ------------- | --------------   |
| network      | UTF-8 String   | Name of an existing network, e.g. "Default" |
| ipAddress    | UTF-8 String   | IPv4 or IPv6 address |
| adapterId    | UTF-8 String   | The ID of the adapter to use for backup, see Appendix A |

#### Return: an error message or ```null```

<p class="vspacer"></p>

### ```Inventory.deleteDevice```

Delete a device from the inventory.

#### Parameters
| Parameter     | Type          | Description      |
| ------------- | ------------- | --------------   |
| network      | UTF-8 String   | Name of an existing network, e.g. "Default" |
| ipAddress    | UTF-8 String   | IPv4 or IPv6 address |

#### Return: ```null```

<p class="vspacer"></p>

### ```Inventory.getDevice```

The ``Inventory.getDevice`` method returns a ``Device`` object as described above, or ``null`` if the requested device does not exist.

#### Parameters
| Parameter     | Type          | Description      |
| ------------- | ------------- | --------------   |
| network       | UTF-8 String   | Name of an existing network, e.g. "Default" |
| ipAddress     | UTF-8 String   | IPv4 or IPv6 address |

#### Return: ```Device``` object or ```null```

#### Device object fields:

| Field         | Type          | Description      |
| ------------- | ------------- | --------------   |
| ipAddress       | UTF-8 String  | IPv4 or IPv6 address |
| hostname        | UTF-8 String  | The hostname of the device |
| adapterId        | UTF-8 String  | The Adapter ID of the device |

```javascript
{  
   "jsonrpc": "2.0",
   "id": 1,
   "result": {
      "ipAddress": "10.0.3.6",
      "hostname": "C2611-2",
      "adapterId": "Cisco::IOS",
      "deviceType": "Router",
      "hardwareVendor": "Cisco",
      "model": "CISCO2611XM-2FE",
      "softwareVendor": "Cisco",
      "osVersion": "12.4(12)",
      "backupStatus": "SUCCESS",
      "complianceState": 0,
      "lastBackup": 1410324618367,
      "lastTelemetry": null,
      "memoSummary": null,
      "custom1": "",
      "custom2": "",
      "custom3": "",
      "custom4": "",
      "custom5": "",
      "network": "Default",
      "serialNumber": "JAE07170Q8S"
   }
}
```

<p class="vspacer"></p>

### ```Inventory.updateDevice```

The ```Inventory.updateDevice``` method is used to update an existing device in the inventory.  It requires only ```network``` and ```ipAddress``` as parameters,
all other parameters are optional.

| Parameter     | Type          | Description      |
| ------------- | ------------- | --------------   |
| network       | UTF-8 String  | Name of the device’s network |
| ipAddress     | UTF-8 String  | IPv4 or IPv6 address |
| newIpAddress  | UTF-8 String  | A new IP address for the device, or null |
| newNetwork    | UTF-8 String  | A new Network name for the device, or null |
| newAdapterId  | UTF-8 String  | A new AdapterId for the device, or null |
| newHostname   | UTF-8 String  | A new Hostname for the device, or null |

#### Return: ```null```

#### Sample Request JSON:

```javascript
{
   "jsonrpc": "2.0",
   "method": "Inventory.updateDevice",
   "params": {
              "network": "Default",
              "ipAddress": "10.0.3.6",
              "newHostname": "router.company.com"
             },
   "id": 1
}
```

<p class="vspacer"></p>

### ```Inventory.updateDevices```

The ```Inventory.updateDevices``` method updates Adapter IDs and/or custom field values for multiple devices in a single operation.

| Parameter     | Type          | Description      |
| ------------- | ------------- | --------------   |
| ipCsv         | UTF-8 String  | A comma separated list of devices of the form IPAddress@network |
| adapterId     | UTF-8 String  | The new adapter ID or ```null``` if it should remain unmodified. |
| customFields  | UTF-8 String Array | An indexed array of custom fields |

The ```ipCsv``` parameter is a comma separated list of devices of the form IPAddress@network (e.g. *192.168.0.254@NetworkA,10.0.0.1@NetworkB*).

The ```adapterId``` parameter is either a new Adapter ID to assign to the specified devices, or ```null``` to leave the device's Adapter ID at their current values.  See *Appendix A* for a list of valid Adapter IDs.

The ```customFields``` parameter is an array of UTF-8 string values.  The first element of the array corresponds to the *Custom 1* custom field, and the fifth element corresponds to the *Custom 5* custom field.  Elements of the ```customFields``` array that are ```null``` will leave the corresponding custom fields at their current values.

#### Return: ```null```

#### Sample Request JSON:

```javascript
{
   "jsonrpc": "2.0",
   "method": "Inventory.updateDevices",
   "params": {
              "ipCsv": "192.168.0.254@NetworkA,192.168.0.252@NetworkA",
              "customFields": ["Tokyo HQ", "Rack 1F-8"]
             },
   "id": 1
}
```

<p class="vspacer"></p>

### ```Inventory.search```

The ```Inventory.search``` method is the fundemental way of retrieving devices from the inventory.  Search supports many criteria, and the criteria can be combined to perform powerful searches.

| Parameter     | Type          | Description      |
| ------------- | ------------- | --------------   |
| network       | UTF-8 String  | Name of the network to search. It is not possible to search across multiple networks in the same operation. |
| scheme        | UTF-8 String  | A single scheme name, or comma-separated list of scheme names (see table below) |
| query         | UTF-8 String  | The query associated with the scheme(s) specified.  If there are multiple schemes specified, the query parameter should contain new-line (\n) characters between each query string |
| pageData      | Object        | A ```PageData``` object defining the offset where retrieval should begin and page size |
| sortColumn    | UTF-8 String  | A string indicating the ```Device``` object attribute the results should be sorted by |
| descending    | Boolean       | A boolean flag indicating whether results should be sorted in descending or ascending order |

The ```scheme``` parameter is a single value or a comma separated list of search schemes from the following table:

| Scheme             | Description     |
| ------------------ | --------------- |
| ipAddress          | Searches the inventory based on a specific IP address (e.g. *192.168.0.254*) or a CIDR (*10.0.0.0/24*) |
| interfaceIpAddress | Searches the inventory based on a specific IP address (e.g. *192.168.0.254*) or a CIDR (*10.0.0.0/24*) where the search includes not only the management IP address but also all of the device interface IP addresses |
| hostname           | Searches the inventory based on a specified hostname.  The specified hostname may be an exact hostname or a name with leading and/or trailing wildcard character (asterisk) |
| adapter            | Searches the inventory based on the specified Adapter ID.  See *Appendix A* for a list of Adapter IDs |
| serial             | Searches the inventory based on a specified serial number.  The specified serial number may be an exact serial number or a string with leading and/or trailing wildcard character (asterisk) |
| status             | Searches the inventory based on the specified inventory status.  The status string (specified in the *query* parameter) must be one of these values: "N" (<i>NONE</i>), "S" (<i>SUCCESS</i>), "C" (<i>COMPLIANCE VIOLATION</i>), "I" (<i>INVALID CREDENTIALS</i>), "F" (<i>OTHER FAILURE</i>) |
| lastChange         | Searches the inventory for devices whose configuration has changed during the specified time period.  Valid values are: "24h", "7d", "30d", or a range in this format: *YYYY-MM-DD/YYYY-MM-DD* (eg. *2012-01-01/2012-06-01*) |
| custom             | Searches the inventory for devices whose custom field values match the specified values. The ```query``` parameter specifies a string that contains a comma-separated list of key/value pairs, i.e "custom2=tokyo*,custom4=12345". The value portion may contain leading and/or trailing wildcard characters. |
| tag                | Searches the inventory for devices which are tagged with the tags specified in the ```query``` parameter.  The ```query``` parameter specifies a string that can contain tag names separated by "AND" or "OR", i.e. "tokyo AND firewall". |

The ```query``` parameter defines the query criteria to be used and is in association with the schemes defined by the ```scheme``` parameter.
For example, if you wish to search based on scheme ```ipAddress``` and ```hostname``` you would specify a ```scheme``` parameter of "ipaddress,hostname", and
a ```query``` parameter of "192.168.0.0/24\ntokyo*".  Note the newline character between the ```ipAddress``` query value and the ```hostname``` query value.

#### Return: A ```PageData``` object

The ```PageData``` object that is returned will contain an attribute called ```devices```, which is an array
of ```Device``` objects.  If the initial ```offset``` that is passed is zero (0), the returned ```PageData```
object will also contain a populated ```total``` attribute, telling you how many total results are available.
By incrementing the ```offset``` by ```pageSize``` you can retrieve subsequent pages of results.
When ```offset``` + ```pageSize``` is greater than or equal to ```total``` there are no more results available.

#### Sample Request JSON:

```javascript
{
   "jsonrpc": "2.0",
   "method": "Inventory.search",
   "params": {
              "network": "Default",
              "scheme": "ipAddress",
              "query": "10.0.3.0/24",
              "pageData": {
                           "offset": 0,
                           "pageSize": 100
                          }
              "sortColumn": "ipAddress",
              "descending": false
             },
   "id": 1
}
```

#### Sample Response JSON:

```javascript
{  
   "jsonrpc": "2.0",
   "id": 1,
   "result": {
      "offset": 0,
      "pageSize": 100,
      "total": 2,
      "devices": [
         {  
            "ipAddress": "10.0.3.1",
            "hostname": "C2611",
            "adapterId": "Cisco::IOS",
            "deviceType": "Router",
            "hardwareVendor": "Cisco",
            "model": "CISCO2611",
            "softwareVendor": "Cisco",
            "osVersion": "12.1(19)",
            "backupStatus": "SUCCESS",
            "complianceState": 0,
            "lastBackup": 1410324616600,
            "lastTelemetry": null,
            "memoSummary": null,
            "custom1": "",
            "custom2": "",
            "custom3": "",
            "custom4": "",
            "custom5": "",
            "network": "Default",
            "serialNumber": "JAB03060AX0"
         },
         {  
            "ipAddress": "10.0.3.6",
            "hostname": "C2611-2",
            "adapterId": "Cisco::IOS",
            "deviceType": "Router",
            "hardwareVendor": "Cisco",
            "model": "CISCO2611XM-2FE",
            "softwareVendor": "Cisco",
            "osVersion": "12.4(12)",
            "backupStatus": "SUCCESS",
            "complianceState": 0,
            "lastBackup": 1410324618367,
            "lastTelemetry": null,
            "memoSummary": null,
            "custom1": "",
            "custom2": "",
            "custom3": "",
            "custom4": "",
            "custom5": "",
            "network": "Default",
            "serialNumber": "JAE07170Q8S"
         }
      ]
   }
}
```

#### Sample Request JSON combining two search schemes:

```javascript
{
   "jsonrpc": "2.0",
   "method": "Inventory.search",
   "params": {
              "network": "Default",
              "scheme": "ipAddress,custom",
              "query": "10.0.3.0/24\ncustom2=New York*,custom4=core",
              "pageData": {
                           "offset": 0,
                           "pageSize": 100
                          }
             },
   "id": 1
}
```

<p class="vspacer"></p>

------------------------------------------------------
