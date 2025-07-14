## Credentials

The credentials API provides the core functionality for device authentication credentials in Net LineDancer.

Methods in this API return various "credentials objects" (e.g. CredentialConfig) which encapsulate attributes of specific credentials in Net LineDancer.  These configuration objects are expressed in JSON format.

<hr>

A *dynamic* ```CredentialConfig``` object is expressed in JSON format seen here:

```json
{  
   "priority": 1,
   "addressSet": {  
      "addresses": [  
         "0.0.0.0/0"
      ]
   },
   "name": "LVI",
   "managedNetwork": "Default",
   "flat": false,
   "type": "DYNAMIC"
}
```

Here is an example of a *static* ``CredentialConfig`` object.  Note the empty ``addresses`` list and ``flat`` value of ``true``:

```json
{  
   "priority": 0,
   "addressSet": {  
      "addresses": [ ]
   },
   "name": "Static",
   "managedNetwork": "Default",
   "flat": true,
   "type": "STATIC"
}
```

| Attribute      | Type          | Description      |
| -------------- | ------------- | --------------   |
| priority       | Integer       | A lower priority number indicates higher placement in the list of credential configurations.  These credentials will be tried before others with a higher number. |
| addressSet     | Object        | A container for "addresses".  Consider this a "fixed" element. |
| addresses      | String Array  | An array of IP Addresses, IP Wildcards, and IP/CIDR expressions the a "dynamic" ``CredentialConfig`` applies to.  *This should be empty for static credential configurations.*
| name           | String  		 | The name of the ``CredentialConfig`` as seen in the user interface. |
| managedNetwork | String  		 | The name of the network that this configuration applies to. If there are no user-created networks this value should be ``Default``. |
| flat*          | Boolean       | ``true`` if the ``CredentialConfig`` represents a "static" configuration, ``false`` if it is dynamic. |
| type  		 | String 		 | Specifies the credential configuration type: STATIC, DYNAMIC and CLOUD. |

<hr>

**_NOTE:_** **: The `flat: Boolean` attribute is deprecated and will soon be removed**

The `type` field is a new attribute introduced to the `CredentialConfig` object to specify the type of credential configuration.

An example of the new ``CredentialSet`` `type` attribute is expressed in JSON format here:


```json
 {
    "priority": 0,
    "addressSet": {
      "addresses": []
    },
    "name": "Static",
    "managedNetwork": "Default",
    "flat": true,
    "type": "STATIC"
  }
  ```

```json
  {
    "priority": 1,
    "addressSet": {
      "addresses": ["0.0.0.0/0"]
    },
    "name": "LVI",
    "managedNetwork": "Default",
    "flat": false,
    "type": "DYNAMIC"
  }
  ```

```json
  {
    "priority": 2,
    "addressSet": {
      "addresses": ["192.168.1.0/24"]
    },
    "name": "CloudConfig",
    "managedNetwork": "Default",
    "flat": false,
    "type": "CLOUD"
  }
  ```

This field will replace the deprecated `flat` attribute, which previously indicated whether a configuration was static (`true`) or dynamic (`false`).

During the transition period, both `flat` and `type` fields will be included in the `getCredentialConfig`, `getAllCredentialConfigs`, and `saveCredentialConfig` APIs. The type field provides a clearer and more extensible way to define credential configurations, accommodating the new "`CLOUD`" credential type alongside existing static and dynamic types.




<hr>

An example ``CredentialSet`` object is expressed in JSON format here:

```json
{
   "name": "Lab Credentials #1",
   "username": "lvi",
   "password": "lvi",
   "enableUsername": "lvi",
   "enablePassword": "lvi",
   "roCommunityString": "public",
   "snmpUsername": "v3user",
   "snmpAuthPassword": "v3pass",
   "snmpPrivPassword": "v3priv",
   "priority": 0
}
```

| Attribute         | Type          | Description      |
| ----------------- | ------------- | --------------   |
| name              | String  | Name of the credential set.  In the case of dynamic credentials this is any user defined name; for static credentials the name MUST be an IP address (IPv4 or IPv6).  |
| username          | String  | The VTY username |
| password          | String  | The VTY password |
| enableUsername    | String  | The enable username |
| enablePassword    | String  | The enable password |
| roCommunityString | String  | The SNMP read-only community string |
| snmpUsername      | String  | The SNMPv3 username |
| snmpAuthPassword  | String  | The SNMPv3 password |
| snmpAuthPriv      | String  | The SNMPv3 private password |
| priority          | Integer       | A lower priority number indicates higher placement in the list of credential sets. These credentials will be tried before others with a higher number. *Inapplicable to static credentials* |

An example ```PageData``` object is expressed in JSON format here:

```json
{
    "offset": 0,
    "pageSize": 10,
    "total": 27,
    "credentialSets": [<CredentialSet> objects]
}
```


| Attribute      | Type          | Description      |
| -------------- | ------------- | --------------   |
| offset         | Integer       | The starting ```offset``` in the results to begin retrieving ```pageSize``` number of ```CredentialSet``` objects. |
| pageSize       | Integer       | The maximum number of ```CredentialSet``` objects to retrieve in a single method call. |
| total          | Integer       | This value is set and retrieved from the server when an ```offset``` of zero (0) is passed.  This indicates the total number of ```CredentialSet``` objects available. |
| credentialSets | Array         | An array of ```CredentialSet``` objects |

<hr>

#### Important Note
Maintaining session is important for this API to work correctly. The first invocation will assign to you a session ID by a cookie called ``JSESSIONID``. Use this cookie to maintain session.

After ``commitEdits`` or ``discardEdits`` is invoked, you may discard this cookie.

<hr>

#### Credentials.commitEdits
Commits edits made in this session.

##### Parameters: none

##### Return: nothing

##### Sample Request JSON:

```json
{
   "jsonrpc": "2.0",
   "method": "Credentials.commitEdits",
   "params": {},
   "id": 1
}
```

<hr>

#### Credentials.discardEdits
Discards edits made in this session.

##### Parameters: none

##### Return: nothing

##### Sample Request JSON:

```json
{
   "jsonrpc": "2.0",
   "method": "Credentials.discardEdits",
   "params": {},
   "id": 1
}
```

<hr>

#### Credentials.getCredentialConfig
Retrieves a single credential configuration ``CredentialConfig`` object.

##### Parameters
| Parameter     | Type          | Description      |
| ------------- | ------------- | --------------   |
| network      | String   | Name of an existing network, e.g. "Default" |
| configName   | String   | Name of a dynamic or static credential configuration |

##### Return: a ``CredentialConfig`` object

##### Sample Request JSON:

```json
{
   "jsonrpc": "2.0",
   "method": "Credentials.getCredentialConfig",
   "params": {
       "network": "Default",
       "configName": "LogicVein"
   },
   "id": 1
}
```

##### Sample Response JSON:

```json
{  
   "jsonrpc": "2.0",
   "id": 1,
   "result": {  
      "priority": 2,
      "addressSet": {
         "addresses": [
            "0.0.0.0/0"
         ]
      },
      "name": "LogicVein",
      "managedNetwork": "Default",
      "flat": false
   }
}
```

<hr>

#### Credentials.saveCredentialConfig

Save a single credential configuration.  This method can be used to save a new configuration, or renaming an existing one.  Note: after call this method you must call the ``commitEdits`` or ``discardEdits`` method.  If you are making many changes, it is recommended that all changes are should be made before a final call to ``commitEdits``.

##### Parameters
| Parameter        | Type          | Description      |
| ---------------- | ------------- | --------------   |
| network          | String  | Name of an existing network, e.g. "Default" |
| oldConfigName    | String  | When *renaming* a credential configuration, this value should be the "old" (original) name of the configuration, and object in the ``credentialConfig`` parameter should contain the new name. This can be ``null`` in all other cases. |
| credentialConfig | Object        | A ``CredentialConfig`` object

##### Return: the updated ``CredentialConfig`` object

##### Sample Request JSON:

```json
{
   "jsonrpc": "2.0",
   "method": "Credentials.saveCredentialConfig",
   "params": {
       "network": "Default",
       "oldConfigName": "LogicVein",
       "credentialConfig": {
           "priority": 1,
           "addressSet": {
               "addresses": [ "0.0.0.0/0" ]
            },
           "name": "LogicVein2",
           "managedNetwork": "Default",
           "flat": false
      },
   "id": 1
}
```

<hr>

#### Credentials.deleteCredentialConfig

Delete a single credential configuration.  Note: after call this method you must call the ``commitEdits`` or ``discardEdits`` method.  If you are making many changes, it is recommended that all changes are should be made before a final call to ``commitEdits``.

##### Parameters
| Parameter     | Type          | Description      |
| ------------- | ------------- | --------------   |
| network      | String   | Name of an existing network, e.g. "Default" |
| configName   | String   | Name of a dynamic or static credential configuration |

##### Return: nothing

##### Sample Request JSON:

```json
{
   "jsonrpc": "2.0",
   "method": "Credentials.deleteCredentialConfig",
   "params": {
       "network": "Default",
       "configName": "LogicVein"
    },
   "id": 1
}
```

<hr>

#### Credentials.getCredentialSets

Get the credential sets associated with a specified credential configuration.

##### Parameters
| Parameter     | Type           | Description      |
| ------------- | -------------- | --------------   |
| pageData      | Object         | A credentials page data object (see above) |
| network       | String   | Name of an existing network, e.g. "Default" |
| configName    | String   | Name of a dynamic or static credential configuration |
| ipOrCidr      | String         | Can be to search among static ``CredentialSets`` based on IP or IP/CIDR, can be "null" |
| sortColumn    | String         | Should be "null" for dynamic configurations, or "ipAddress" for static credential configurations |
| descending    | Boolean        | The sort order of the ``CredentialSet`` objects, only applicable to static configurations |

##### Return: A ``PageData`` object containing a collection of ``CredentialSet`` objects

The ```PageData``` object that is returned will contain a property called ```credentialSets```, which is an array of ```CredentialSet``` objects.  If the initial ```offset``` that is passed is zero (0),
the returned ```PageData``` object will also contain a populated ```total``` attribute, telling you how many total results are available.  By incrementing the ```offset``` by ```pageSize``` you can
retrieve subsequent pages of results.  When ```offset``` + ```pageSize``` is greater than or equal to ```total``` there are no more results available.

##### Sample Request JSON:

```json
{
   "jsonrpc": "2.0",
   "method": "Credentials.getCredentialSets",
   "params": {
      "pageData": {
          "offset": 0,
          "pageSize": 10,
          "total": 0,
          "credentialSets": [ ]
       },
      "network": "Default",
      "configName": "LogicVein",
      "ipOrCidr": null,
      "sortColumn": "ipAddress",
      "descending": false
     },
   "id": 1
}
```

##### Sample Response JSON:

```json
{
   "jsonrpc": "2.0",
   "id": 1,
   "result": {
      "offset": 0,
      "pageSize": 10,
      "total": 2,
      "credentialSets": [
         {
            "name": "Lab Credentials #1",
            "username": "lvi",
            "password": "lvi",
            "enableUsername": "lvi",
            "enablePassword": "lvi",
            "roCommunityString": "public",
            "snmpUsername": "",
            "snmpAuthPassword": "",
            "snmpPrivPassword": "",
            "priority": 0
         },
         {
            "name": "Lab Credentials #2",
            "username": "test",
            "password": "test",
            "enableUsername": "test",
            "enablePassword": "test",
            "roCommunityString": "public",
            "snmpUsername": "test",
            "snmpAuthPassword": "test",
            "snmpPrivPassword": "test",
            "priority": 1
         }
      ]
   }
}
```

*Static* credential sets will look identical to *dynamic* credential sets with the exception that the ``name`` property will contain the IP address of the device that the credential set is associated with.

<hr>

#### Credentials.saveCredentialSets

Save a collection of credential sets.  Note: after call this method you must call the ``commitEdits`` or ``discardEdits`` method.  If you are making many changes, it is recommended that all changes are
should be made before a final call to ``commitEdits``.

##### Parameters
| Parameter        | Type          | Description      |
| ---------------- | ------------- | --------------   |
| network          | String  | Name of an existing network, e.g. "Default" |
| configName       | String  | Name of a dynamic or static credential configuration |
| credentialSets   | Array         | An array of ``CredentialSet`` objects |

##### Return: nothing

##### Sample Request JSON:

```json
{
   "jsonrpc": "2.0",
   "method": "Credentials.saveCredentialSets",
   "params": {
       "network": "Default",
       "configName": "LogicVein",
       "credentialSets": [
           {
              "name": "Lab Credentials #1",
              "username": "newUsername",
              "password": "lvi",
              "enableUsername": "newEnable",
              "enablePassword": "lvi",
              "roCommunityString": "public",
              "snmpUsername": "",
              "snmpAuthPassword": "",
              "snmpPrivPassword": "",
              "priority": 0
           }
       ]
    },
   "id": 1
}
```

<hr>

#### Credentials.deleteCredentialSets

Delete a collection of credential sets.  Note: after call this method you must call the ``commitEdits`` or ``discardEdits`` method.  If you are making many changes, it is recommended that all changes are should be made before a final call to ``commitEdits``.

##### Parameters
| Parameter        | Type          | Description      |
| ---------------- | ------------- | --------------   |
| network          | String  | Name of an existing network, e.g. "Default" |
| configName       | String  | Name of a dynamic or static credential configuration |
| credentialSets   | Array         | An array of ``CredentialSet`` objects |

##### Return: nothing

##### Sample Request JSON:

```json
{
   "jsonrpc": "2.0",
   "method": "Credentials.deleteCredentialSets",
   "params": {
      "network": "Default",
      "configName": "LogicVein",
      "credentialSets": [
           {
              "name": "Old Credentials #1",
              "username": "lvi",
              "password": "lvi",
              "enableUsername": "newEnable",
              "enablePassword": "lvi",
              "roCommunityString": "public",
              "snmpUsername": "",
              "snmpAuthPassword": "",
              "snmpPrivPassword": "",
              "priority": 0
           },
           {
              "name": "Old Credentials #2",
              "username": "test",
              "password": "test",
              "enableUsername": "test",
              "enablePassword": "test",
              "roCommunityString": "public",
              "snmpUsername": "",
              "snmpAuthPassword": "",
              "snmpPrivPassword": "",
              "priority": 1
           }
       ]
    }
   "id": 1
}
```
