Networks
--------

The networks API provides the functionality for managing the managed network definitions.

See the `Objects <#objects>`__ section for a description of the various objects consumed and returned by these APIs.

Methods
~~~~~~~

.. _networksdefinemanagednetwork:

Networks.defineManagedNetwork
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create a new Managed Network within the system.

Parameters
''''''''''

=========== ====== ============================
Parameter   Type   Description
=========== ====== ============================
networkName String The network name
bridgeName  String The name of the smart bridge
=========== ====== ============================

Return: void
''''''''''''

.. _networksgetmanagednetwork:

Networks.getManagedNetwork
^^^^^^^^^^^^^^^^^^^^^^^^^^

Get the Managed Network identified by name.

.. _parameters-1:

Parameters
''''''''''

=========== ====== ================
Parameter   Type   Description
=========== ====== ================
networkName String The network name
=========== ====== ================

Return: A `ManagedNetwork <#managednetwork>`__ object
'''''''''''''''''''''''''''''''''''''''''''''''''''''

.. _networksgetmanagednetworknames:

Networks.getManagedNetworkNames
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Get the names of the Managed Networks that have been defined.

.. _parameters-2:

Parameters
''''''''''

None

Return: An array of Strings
'''''''''''''''''''''''''''

.. _networksgetallmanagednetworks:

Networks.getAllManagedNetworks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Get a list of all Managed Networks that have been defined.

.. _parameters-3:

Parameters
''''''''''

None

Return: An array of `ManagedNetwork <#managednetwork>`__ objects
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

.. _networksdeletemanagednetwork:

Networks.deleteManagedNetwork
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Delete a Managed Network identified by the name.

.. _parameters-4:

Parameters
''''''''''

=========== ====== ================
Parameter   Type   Description
=========== ====== ================
networkName String The network name
=========== ====== ================

.. _return-void-1:

Return: void
''''''''''''

.. _networksupdatemanagednetwork:

Networks.updateManagedNetwork
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Update a Managed Network's information using the contents of the supplied ManagedNetwork instance. This instance must encapsulate information about a Managed Network that actually exists, otherwise an exception is thrown.

.. _parameters-5:

Parameters
''''''''''

========= ==================================== =====================
Parameter Type                                 Description
========= ==================================== =====================
network   `ManagedNetwork <#managednetwork>`__ The network to update
========= ==================================== =====================

.. _return-void-2:

Return: void
''''''''''''

.. _networksgetmanagednetworksbybridge:

Networks.getManagedNetworksByBridge
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Get all managed networks by bridge.

.. _parameters-6:

Parameters
''''''''''

========== ====== =====================
Parameter  Type   Description
========== ====== =====================
bridgeName String The smart bridge name
========== ====== =====================

.. _return-an-array-of-managednetwork-objects-1:

Return: An array of `ManagedNetwork <#ManagedNetwork>`__ objects
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

Objects
~~~~~~~

ManagedNetwork
^^^^^^^^^^^^^^

========== ======= =======================================
Attribute  Type    Description
========== ======= =======================================
name       String  The managed network name
bridgeName String  The name of the associated smart bridge
online     Boolean The current online state of the bridge
========== ======= =======================================
