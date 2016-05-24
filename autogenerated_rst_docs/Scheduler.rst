Scheduler
~~~~~~~~~

**NOTE: This API has significant and incompatible changes in the next major release. You will need to update any scripts that use these APIs.**

The scheduler API provides access to job management, scheduling and execution. Job types include tools, configuration backup, Smart Changes, and reports.

See the `Scheduler Objects <#scheduler-objects>`__ section for a description of the various objects consumed and returned by these APIs.

Scheduler.addJob
^^^^^^^^^^^^^^^^

Save (or replace) the job defined by the specified ``JobData``.

Parameters
''''''''''

+-------------+-----------+----------------------------------------------------------------------------+
| Parameter   | Type      | Description                                                                |
+=============+===========+============================================================================+
| jobData     | JobData   | A ``JobData`` job definition object                                        |
+-------------+-----------+----------------------------------------------------------------------------+
| replace     | Boolean   | *true* if an existing job with the same name replaced, *false* otherwise   |
+-------------+-----------+----------------------------------------------------------------------------+

Return: the ``JobData`` object with ``jobId`` property populated.
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

.. raw:: html

   <hr>

Scheduler.deleteJob
^^^^^^^^^^^^^^^^^^^

Delete the specified job.

Parameters
''''''''''

+------------------+----------+-------------------------------------------------------+
| Parameter        | Type     | Description                                           |
+==================+==========+=======================================================+
| managedNetwork   | String   | The name of the network in which the job is defined   |
+------------------+----------+-------------------------------------------------------+
| jobName          | String   | The name of the job to delete                         |
+------------------+----------+-------------------------------------------------------+

Return: ``true`` if the Job was deleted successfully, ``false`` otherwise
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

.. raw:: html

   <hr>

Scheduler.getJob
^^^^^^^^^^^^^^^^

Get the ``JobData`` for the specified device.

Parameters
''''''''''

+------------------+----------+-------------------------------------------------------+
| Parameter        | Type     | Description                                           |
+==================+==========+=======================================================+
| managedNetwork   | String   | The name of the network in which the job is defined   |
+------------------+----------+-------------------------------------------------------+
| jobName          | String   | The name of the job                                   |
+------------------+----------+-------------------------------------------------------+

Return: a ``JobData`` object.
'''''''''''''''''''''''''''''

.. raw:: html

   <hr>

Scheduler.scheduleJob
^^^^^^^^^^^^^^^^^^^^^

Create a "trigger" (schedule) for a job.

Parameters
''''''''''

+---------------+---------------+-------------------------------------+
| Parameter     | Type          | Description                         |
+===============+===============+=====================================+
| triggerData   | TriggerData   | The schedule (trigger) definition   |
+---------------+---------------+-------------------------------------+

Return: an updated ``TriggerData`` object.
''''''''''''''''''''''''''''''''''''''''''

.. raw:: html

   <hr>

Scheduler.unscheduleJob
^^^^^^^^^^^^^^^^^^^^^^^

Delete a "trigger" (schedule) for a job.

Parameters
''''''''''

+------------------+----------+------------------------------------------------------------+
| Parameter        | Type     | Description                                                |
+==================+==========+============================================================+
| managedNetwork   | String   | The name of the network in which the schedule is defined   |
+------------------+----------+------------------------------------------------------------+
| triggerData      | String   | The schedule (trigger) name                                |
+------------------+----------+------------------------------------------------------------+
| jobName          | String   | The name of the job                                        |
+------------------+----------+------------------------------------------------------------+

Return: a boolean, *true* if the trigger was found and deleted.
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

.. raw:: html

   <hr>

Scheduler.runNow
^^^^^^^^^^^^^^^^

Execute a job defined by the specified ``JobData``.

Parameters
''''''''''

+-------------+-----------+---------------------------------------+
| Parameter   | Type      | Description                           |
+=============+===========+=======================================+
| jobData     | JobData   | A ``JobData`` job definition object   |
+-------------+-----------+---------------------------------------+

Return: an ``ExecutionData`` object.
''''''''''''''''''''''''''''''''''''

.. raw:: html

   <hr>

Scheduler.runExistingJobNow
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Execute a job defined by the specified ``JobData``.

Parameters
''''''''''

+------------------+----------+-------------------------------------------------------+
| Parameter        | Type     | Description                                           |
+==================+==========+=======================================================+
| managedNetwork   | String   | The name of the network in which the job is defined   |
+------------------+----------+-------------------------------------------------------+
| jobName          | String   | The name of the job to run                            |
+------------------+----------+-------------------------------------------------------+

Return: an ``ExecutionData`` object.
''''''''''''''''''''''''''''''''''''

.. raw:: html

   <hr>

Scheduler.getExecutionDetails
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Get paged ``ExecutionData`` objects representing the execution history of jobs in the scheduler.

Parameters
''''''''''

+--------------+---------------------+----------------------------------------------------------------------------------------+
| Parameter    | Type                | Description                                                                            |
+==============+=====================+========================================================================================+
| pageData     | ExecutionPageData   | Page object for execution data                                                         |
+--------------+---------------------+----------------------------------------------------------------------------------------+
| sortColumn   | String              | The name of an ``ExecutionData`` attribute to sort by, *null* for default sort order   |
+--------------+---------------------+----------------------------------------------------------------------------------------+
| descending   | Boolean             | *true* if the sort should be descending                                                |
+--------------+---------------------+----------------------------------------------------------------------------------------+

Return: an updated ``ExecutionPageData`` object.
''''''''''''''''''''''''''''''''''''''''''''''''

.. raw:: html

   <hr>

Scheduler Objects
~~~~~~~~~~~~~~~~~

JobData
^^^^^^^

+------------------+----------+--------------------------------------------------------------------------------------------------+
| Field            | Type     | Description                                                                                      |
+==================+==========+==================================================================================================+
| jobName          | String   | The name of the job                                                                              |
+------------------+----------+--------------------------------------------------------------------------------------------------+
| description      | String   | The description of the job                                                                       |
+------------------+----------+--------------------------------------------------------------------------------------------------+
| managedNetwork   | String   | The name of the network in which the job is defined                                              |
+------------------+----------+--------------------------------------------------------------------------------------------------+
| jobType          | String   | One of the pre-defined NetLD job types (see below)                                               |
+------------------+----------+--------------------------------------------------------------------------------------------------+
| jobParameters    | Map      | A map (hash) of job parameter name/value pairs that are specific to each *jobType* (see below)   |
+------------------+----------+--------------------------------------------------------------------------------------------------+

TriggerData
^^^^^^^^^^^

+------------------+----------+----------------------------------------------------------------------+
| Field            | Type     | Description                                                          |
+==================+==========+======================================================================+
| triggerName      | String   | The name of the schedule (trigger)                                   |
+------------------+----------+----------------------------------------------------------------------+
| jobName          | String   | The name of the job                                                  |
+------------------+----------+----------------------------------------------------------------------+
| jobNetwork       | String   | The name of the network in which the schedule (trigger) is defined   |
+------------------+----------+----------------------------------------------------------------------+
| timeZone         | String   | The timezone name                                                    |
+------------------+----------+----------------------------------------------------------------------+
| cronExpression   | String   | The cron expression                                                  |
+------------------+----------+----------------------------------------------------------------------+

ExecutionData
^^^^^^^^^^^^^

+-------------------+------------------+-------------------------------------------------------+
| Field             | Type             | Description                                           |
+===================+==================+=======================================================+
| id                | Integer          | The execution ID                                      |
+-------------------+------------------+-------------------------------------------------------+
| jobName           | String           | The name of the job                                   |
+-------------------+------------------+-------------------------------------------------------+
| managedNetwork    | String           | The name of the network in which the job is defined   |
+-------------------+------------------+-------------------------------------------------------+
| executor          | String           | The username of the user who executed the job         |
+-------------------+------------------+-------------------------------------------------------+
| startTime         | 64-bit Integer   | The start time of the job as a Unix epoch value       |
+-------------------+------------------+-------------------------------------------------------+
| endTime           | 64-bit Integer   | The end time of the job as a Unix epoch value         |
+-------------------+------------------+-------------------------------------------------------+
| completionState   | Integer          | 0=normal, 1=cancelled, 2=misfired (schedule missed)   |
+-------------------+------------------+-------------------------------------------------------+
| status            | String           | One of: "OK", "WARN", "ERROR", "ABORT"                |
+-------------------+------------------+-------------------------------------------------------+

ExecutionPageData
^^^^^^^^^^^^^^^^^

+-----------------+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Attribute       | Type      | Description                                                                                                                                                                                                                              |
+=================+===========+==========================================================================================================================================================================================================================================+
| offset          | Integer   | The starting ``offset`` in the results to begin retrieving ``pageSize`` number of ``ExecutionData`` objects.                                                                                                                             |
+-----------------+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| pageSize        | Integer   | The maximum number of ``ExecutionData`` objects to retrieve in a single method call.                                                                                                                                                     |
+-----------------+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| total           | Integer   | This value is set and retrieved from the server when an ``offset`` of zero (0) is passed. This indicates the total number of ``ExecutionData`` objects available. This value is ignored when ``ExecutionData`` is used as a parameter.   |
+-----------------+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| executionData   | Array     | An array of ``ExecutionData`` objects. This value is ignored (and optional) when ``ExecutionPageData`` is used as a parameter.                                                                                                           |
+-----------------+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

.. raw:: html

   <hr>

Job Types
^^^^^^^^^

+--------------------------+-------------------------------------------+
| Type Name                | Type Description                          |
+==========================+===========================================+
| "Backup Configuration"   | Network device configuration backup.      |
+--------------------------+-------------------------------------------+
| "Bulk Update"            | SmartChange execution.                    |
+--------------------------+-------------------------------------------+
| "Discover Devices"       | Network device discovery.                 |
+--------------------------+-------------------------------------------+
| "Script Tool Job"        | Pre-definied read/write tool execution.   |
+--------------------------+-------------------------------------------+

Job Parameters (per Job Type)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Job parameters are stored in a map (hash) of string name/value pairs. **All job parameter names and values are UTF-8 strings**. Even "Boolean" and "Integer" values should be stored as strings such as *"true"* or *"5432"*.

*Most* (but not all) jobs share a common set of "device resolution" parametersused to specify the set of devices that the job applies to (see `Device Resolution Parameters <#device-resolution-parameters>`__)

Device Resolution Parameters
''''''''''''''''''''''''''''

The documentation below for each specific type will declare whether these values are applicable.

+----------------------+----------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name                 | Type     | Value Description                                                                                                                                                                                                                                                                    |
+======================+==========+======================================================================================================================================================================================================================================================================================+
| ipResolutionScheme   | String   | A single scheme name, or comma-separated list of scheme names. See ``Inventory.search`` for documentation regarding supported values.                                                                                                                                                |
+----------------------+----------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ipResolutionData     | String   | The query associated with the scheme(s) specified. If there are multiple schemes specified, the query parameter should contain new-line (\\n) characters between each query scheme query string. See ``Inventory.search`` documentation for examples of multi-scheme query values.   |
+----------------------+----------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| managedNetwork       | String   | The name of the network in which the devices are resolved. This value should be the same as the ``managedNetwork`` defined in the ``JobData`` object.                                                                                                                                |
+----------------------+----------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

"Backup Configuration"
''''''''''''''''''''''

-  The *only* job parameters required for this job are the (`Device Resolution Parameters <#device-resolution-parameters>`__).

Ruby example:

.. code:: ruby

    job = {
        'managedNetwork' => 'Headquarters',
        'jobName' => "HQ backup",
        'jobType' => 'Backup Configuration',
        'description' => '',
        'jobParameters' => {
            'ipResolutionScheme' => 'ipAddress',
            'ipResolutionData' => '192.168.0.0/16',
            'managedNetwork' => 'Headquarters'
        },
    }

    execution = netld['Scheduler.runNow', job]

"Bulk Update"
'''''''''''''

-  *Device resolution parameters required.*

In version 14.06 `Scheduler.addJob <#scheduler.addjob>`__ is not supported for this job type. Only `Scheduler.runExistingJobNow <#scheduler.runexistingjobnow>`__ is currently supported. This means that the SmartChange ("bulk update") must first be created through the browser user interface.

+-------------------+----------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name              | Type     | Value Description                                                                                                                                                  |
+===================+==========+====================================================================================================================================================================+
| replacementMode   | String   | Valid values are: "perdevice" or "perjob".                                                                                                                         |
+-------------------+----------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| templateXml       | String   | This string property should be copied verbatim from the ``JobData`` object for the SmartChange, retrieved from the `Scheduler.getJob <#scheduler.getjob>`__ API.   |
+-------------------+----------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| replacements      | String   | An XML string defining the replacement values to be applied to the SmartChange template. See the documentation below for specific format.                          |
+-------------------+----------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------+

The "replacements" XML content is very similar between ``perdevice`` and ``perjob`` type SmartChanges.

In the "perjob" case, there is a single ``<config>`` tag defined, containing a ``<replacement>`` tag for each replacement defined in the SmartChange template. The *"name"* attribute of a ``<replacement>`` tag must match exactly the name of a replacement defined in the template. The *"value"* expressed between the opening and closing ``<replacement>`` tags
must be a Base64 encoded value. This is the value that will be substituted in the template before execution.

**Per-job example replacements XML**

.. code:: xml

    <configs>
      <config>
        <replacement name="IP Address">MTkyLjE2OC4wLjI1NA==</replacement>
        <replacement name="VLAN ID">MTAw</replacement>
      </config>
    </configs>

The "perdevice" replacements XML is similar to the "perjob" XML, with two notable exceptions. The ``<config>`` tag must now contain a *"device"* attribute whose value is the IP address of the device, followed by an ``@`` character, and finally a managed network name. Note that if the SmartChange job definition was created in a network called "Headquarters",
then a device that is defined to be in another networks, e.g. *%2210.0.0.1@Default%22*, will be ignored.

The second difference from a "perjob" XML definition is that there is one ``<config>`` and set of ``<replacement>`` tags for *each* device in the job.

**Per-device example replacements XML**

.. code:: xml

    <configs>
      <config device="10.0.0.211@Default">
        <replacement name="IP Address">MTkyLjE2OC4wLjI2NB==</replacement>
        <replacement name="VLAN ID">MTIzNA==</replacement>
      </config>
      <config device="10.0.2.3@Default">
        <replacement name="IP Address">aWprbA==</replacement>
        <replacement name="VLAN ID">OTAxMg==</replacement>
      </config>
    </configs>

*Note: the replacements names of "IP Address" and "VLAN ID" are merely example replacement names, not pre-defined or required names.*

"Discover Devices"
''''''''''''''''''

-  *Device resolution parameters not required.*

+--------------------+----------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name               | Type     | Value Description                                                                                                                                                                |
+====================+==========+==================================================================================================================================================================================+
| communityStrings   | String   | Additional SNMP community string or comma-separated list of strings                                                                                                              |
+--------------------+----------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| boundaryNetworks   | String   | Comma-separated list of discovery boundary networks (CIDR)                                                                                                                       |
+--------------------+----------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| crawl              | String   | A "boolean" value indicating whether the discovery should use neighbor/peer information to discover additional devices                                                           |
+--------------------+----------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| includeInventory   | String   | A "boolean" value indicating whether the discovery should automatically include current inventory devices. This option is only meaningful when "crawl" is also set to *"true"*   |
+--------------------+----------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| addresses          | String   | A comma-separated list of IP address "shapes" to include in the discovery. See below.                                                                                            |
+--------------------+----------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Python example:

.. code:: python

    job_data = {
        'managedNetwork': 'Headquarters',
        'jobName': 'Discover lab devices',
        'jobType': 'Discover Devices',
        'description': '',
        'jobParameters': {
            'addresses': '10.0.0.0/24,10.0.1.0/24',
            'managedNetwork': 'Headquarters',
            'crawl': 'false',
            'boundaryNetworks': '10.0.0.0/8,192.168.0.0/16,172.16.0.0/12',
            'includeInventory': 'false',
            'communityStrings': 'public'
        }
    }

    execution = netld_svc.call('Scheduler.runNow', job_data)

Job Detail Retrieval
~~~~~~~~~~~~~~~~~~~~
