Configuration
-------------

The configuration API provides the core functionality of retrieving configuration history and managing draft configurations.

Methods in this API return various "configuration objects" (e.g. ChangeLog) which encapsulate attributes of configuration history in Net LineDancer. These configuration objects are expressed in JSON format. The following JSON objects are returned by these APIs.

A ``Change`` object is expressed in JSON format seen here:

.. code:: javascript

   {
       "author": "smith",
       "path": "/running-config",
       "mimeType": "test-plain",
       "type": "A",
       "size": 4321,
       "previousChange": 1361241698,
       "revisionTime": 1361249887,
       "head": true,
       "hasMemo": false,
       "mappingType": "backup",
       "mappingId": "31"
   }

.. raw:: html

   <p></p>

============== ======= =================================================================================================================================================================================
Attribute      Type    Description
============== ======= =================================================================================================================================================================================
author         String  The netLD username who made the change that was recorded, if known. 'n/a' if not available.
path           String  The filesystem path of the configuration on the device
mimeType       String  The MIME-type of the configuration file. Possible values are 'text/plain', 'application/octet-stream' (binary), 'application/x-tar' (binary).
type           String  The kind of change recorded. Possible values are 'M' (modification to existing configuration), 'A' (addition of a never before seen configuration), 'D' (a deleted configuration)
size           Integer The size of the configuration in bytes
previousChange Integer The timestamp of the previous configuration revision in milliseconds (in Unix Epoch time). Can be null.
revisionTime   Integer The timestamp when the configuration was backed up, in milliseconds (in Unix Epoch time).
head           Boolean "true" if this revision is the latest, "false" otherwise.
hasMemo        Boolean "true" is there is a memo for this configuration, "false" otherwise.
mappingType    String  undocumented.
mappingId      String  undocumented.
============== ======= =================================================================================================================================================================================

.. raw:: html

   <p></p>

A ``ChangeLog`` object is expressed in JSON format seen here:

.. code:: javascript

   {
       "timestamp": 2311232341,
       "changes": [<Change> objects]
   }

.. raw:: html

   <p></p>

========= ======= =========================================================================================================
Attribute Type    Description
========= ======= =========================================================================================================
timestamp Integer The 'Unix Epoch' timestamp (in milliseconds) when the configuration was recorded
changes   Array   An array of ``Change`` objects, reflecting configurations that were captured at the same time (timestamp)
========= ======= =========================================================================================================

.. raw:: html

   <p></p>

A ``PageData`` object is expressed in JSON format seen here:

.. code:: javascript

   {
       "offset": 0,
       "pageSize": 10,
       "total": 27,
       "changeLogs": [<ChangeLog> objects]
   }

========== ======= =============================================================================================================================================================
Attribute  Type    Description
========== ======= =============================================================================================================================================================
offset     Integer The starting ``offset`` in the results to begin retrieving ``pageSize`` number of ``ChangeLog`` objects.
pageSize   Integer The maximum number of ``ChangeLog`` objects to retrieve in a single method call.
total      Integer This value is set and retrieved from the server when an ``offset`` of zero (0) is passed. This indicates the total number of ``ChangeLog`` objects available.
changeLogs Array   An array of ``ChangeLog`` objects
========== ======= =============================================================================================================================================================

.. raw:: html

   <p></p>

A ``Revision`` object is expressed in JSON format seen here:

.. code:: javascript

   {
       "path": "/running-config",
       "author": "n/a",
       "mimeType": "text/plain",
       "size": 4321,
       "previousChange": 1361241698,
       "content": <BASE64 ENCODED STIRING>
   }

============== ======= =============================================================================================================================================
Attribute      Type    Description
============== ======= =============================================================================================================================================
path           String  The filesystem path of the configuration on the device
author         String  The netLD username who made the change that was recorded, if known. 'n/a' if not available.
mimeType       String  The MIME-type of the configuration file. Possible values are 'text/plain', 'application/octet-stream' (binary), 'application/x-tar' (binary).
size           Integer The size of the configuration in bytes
previousChange Integer The timestamp of the previous configuration revision in milliseconds (in Unix Epoch time). Can be null.
content        String  The configuration file content, encoded in Base64 format
============== ======= =============================================================================================================================================

.. _configurationretrievesnapshotchangelog:

Configuration.retrieveSnapshotChangeLog
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Retrieves the configuration history for the specified device.

Parameters
''''''''''

========= =========== ==========================================================================
Parameter Type        Description
========= =========== ==========================================================================
network   String      Name of an existing network, e.g. "Default"
ipAddress String      IPv4 or IPv6 address
pageData  JSON Object A ``PageData`` object specifying the starting ``offset`` and ``pageSize``.
========= =========== ==========================================================================

Return: a ``PageData`` object
'''''''''''''''''''''''''''''

Sample Request JSON:
''''''''''''''''''''

.. code:: javascript

   {
      "jsonrpc": "2.0",
      "method": "Configuration.retrieveSnapshotChangeLog",
      "params": {
                 "network": "Default",
                 "ipAddress": "192.168.0.254",
                 "pageData": {
                              "offset": 0,
                              "pageSize": 10
                             }
                },
      "id": 1
   }

The ``PageData`` object that is returned will contain an attribute called ``changeLogs``, which is an array of ``ChangeLog`` objects. If the initial ``offset`` that is passed is zero (0), the returned ``PageData`` object will also contain a populated ``total`` attribute, telling you how many total results are available. By incrementing the ``offset`` by
``pageSize`` you can retrieve subsequent pages of results. When ``offset`` + ``pageSize`` is greater than or equal to ``total`` there are no more results available.

Sample Response JSON:
'''''''''''''''''''''

.. code:: javascript

   {  
      "jsonrpc": "2.0",
      "id": 1,
      "result": {
         "offset": 0,
         "pageSize": 10,
         "total": 1,
         "changeLogs": [
            {
               "changes":[
                  {
                     "author": "brettw",
                     "path": "/running-config",
                     "mimeType": "text/plain",
                     "type": "A",
                     "size": 1601,
                     "previousChange": 1400922143000,
                     "revisionTime": 1410324618000,
                     "mappingType": "backup",
                     "mappingId": 4,
                     "hasMemo": false,
                     "file": false,
                     "head": true
                  },
                  {  
                     "author": "brettw",
                     "path": "/startup-config",
                     "mimeType": "text/plain",
                     "type": "A",
                     "size": 1601,
                     "previousChange": 1400922143000,
                     "revisionTime": 1410324618000,
                     "mappingType": "backup",
                     "mappingId": 4,
                     "hasMemo": false,
                     "file": false,
                     "head": true
                  }
               ],
               "timestamp": 1410324618000
            }
         ]
      }
   }

.. raw:: html

   <hr>

.. _configurationretrieverevision:

Configuration.retrieveRevision
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Retrieve a revision of a configuration for the specified device.

.. _parameters-1:

Parameters
''''''''''

========== ======= =========================================================================================================================================================================================================================================================================
Parameter  Type    Description
========== ======= =========================================================================================================================================================================================================================================================================
network    String  Name of an existing network, e.g. "Default"
ipAddress  String  IPv4 or IPv6 address
configPath String  The path of the configuration file to retrieve. This should be the same value as the ``path`` attribute in a ``Change`` object.
timestamp  Integer The timestamp (in Unix Epoch milliseconds) of the configuration to retrieve. This should be the same value as the ``revisionTime`` attribute in a ``Change`` object returned by ``retrieveSnapshotChangeLog``. If timestamp is omitted, the latest revision is retrieved.
========== ======= =========================================================================================================================================================================================================================================================================

Return: a ``Revision`` object
'''''''''''''''''''''''''''''

.. _sample-request-json-1:

Sample Request JSON:
''''''''''''''''''''

.. code:: javascript

   {
      "jsonrpc": "2.0",
      "method": "Configuration.retrieveRevision",
      "params": {
                 "network": "Default",
                 "ipAddress": "192.168.0.254",
                 "configPath": "/running-config",
                 "timestamp": 1410324618000
                },
      "id": 1
   }

.. _sample-response-json-1:

Sample Response JSON:
'''''''''''''''''''''

.. code:: javascript

   {  
      "jsonrpc": "2.0",
      "id": 1,
      "result": {  
         "lastChanged": 1410324618000,
         "path": "/running-config",
         "author": "brettw",
         "mimeType": "text/plain",
         "size": 1601,
         "prevChange": null,
         "runStart": 0,
         "content": <Base64 encoded string>
      }
   }
