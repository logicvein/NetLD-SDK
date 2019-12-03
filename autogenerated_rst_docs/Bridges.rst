Bridges
-------

The bridges API provides the functionality of managing the smart bridge settings.

Objects
~~~~~~~

.. _bridges-1:

Bridges
^^^^^^^

========= ======= ============================================================================================================================================
Attribute Type    Description
========= ======= ============================================================================================================================================
bridgeId  Integer The database ID of the bridge
name      String  The SmartBridge name
hostOrIp  String  The host or IP address of the smart bridge
port      Integer The port to connect to the smart bridge on.
inbound   Boolean True if the smart bridge initiates the connection to the core server, false if the core server initiates the connection to the smart bridge.
token     String  The authentication token used for connecting to the smart bridge.
========= ======= ============================================================================================================================================

Methods
~~~~~~~

.. _bridgesdefinebridge:

Bridges.defineBridge
^^^^^^^^^^^^^^^^^^^^

Create a new network bridge within the system.

Parameters
''''''''''

========== ======= ============================================================================================================================================
Parameter  Type    Description
========== ======= ============================================================================================================================================
bridgeName String  The SmartBridge name
hostOrIp   String  The host or IP address of the smart bridge
port       String  The port to connect to the smart bridge on.
inbound    Boolean True if the smart bridge initiates the connection to the core server, false if the core server initiates the connection to the smart bridge.
token      String  The authentication token used for connecting to the smart bridge.
========== ======= ============================================================================================================================================

Return: void
''''''''''''

.. _bridgesgetbridge:

Bridges.getBridge
^^^^^^^^^^^^^^^^^

Get a bridge by name.

.. _parameters-1:

Parameters
''''''''''

========== ====== ====================
Parameter  Type   Description
========== ====== ====================
bridgeName String The SmartBridge name
========== ====== ====================

Return: A ``Bridge`` object
'''''''''''''''''''''''''''

.. _bridgesgetallbridges:

Bridges.getAllBridges
^^^^^^^^^^^^^^^^^^^^^

Get all of the defined bridges.

.. _parameters-2:

Parameters
''''''''''

None

Return: An array of ``Bridge`` objects
''''''''''''''''''''''''''''''''''''''

.. _bridgesdeletebridge:

Bridges.deleteBridge
^^^^^^^^^^^^^^^^^^^^

Delete the bridge definition with the specified name

.. _parameters-3:

Parameters
''''''''''

========== ====== ====================
Parameter  Type   Description
========== ====== ====================
bridgeName String The SmartBridge name
========== ====== ====================

.. _return-void-1:

Return: void
''''''''''''

.. _bridgesupdatebridge:

Bridges.updateBridge
^^^^^^^^^^^^^^^^^^^^

Get a bridge by name.

.. _parameters-4:

Parameters
''''''''''

========= ====== ===============================
Parameter Type   Description
========= ====== ===============================
bridge    Bridge The bridge definition to update
========= ====== ===============================

.. _return-void-2:

Return: void
''''''''''''
