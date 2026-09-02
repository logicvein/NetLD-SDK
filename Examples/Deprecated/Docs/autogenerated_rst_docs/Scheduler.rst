Scheduler
---------

The scheduler API provides access to job management, scheduling and execution. Job types include tools, configuration backup, Smart Changes, and reports.

.. _schedulerrunnow:

Scheduler.runNow
^^^^^^^^^^^^^^^^

Execute a job defined by the specified ``JobData``.

Parameters
''''''''''

========= =========== ====================
Parameter Type        Description
========= =========== ====================
jobData   JSON Object A ``JobData`` object
========= =========== ====================

.. _return-an-executiondata-object:

Return: an ``ExecutionData`` object.
''''''''''''''''''''''''''''''''''''

..

--------------

.. _schedulersavejob:

Scheduler.saveJob
^^^^^^^^^^^^^^^^^

Save (or replace) the job defined by the specified ``JobData``.

.. _parameters-1:

Parameters
''''''''''

========= =========== ====================
Parameter Type        Description
========= =========== ====================
jobData   JSON Object A ``JobData`` object
========= =========== ====================

.. _return-the-jobdata-object-with-jobid-property-populated:

Return: the ``JobData`` object with ``jobId`` property populated.
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

.. _schedulerdeletejob:

Scheduler.deleteJob
^^^^^^^^^^^^^^^^^^^

Delete a job by ID.

.. _parameters-2:

Parameters
''''''''''

========= ======= =================
Parameter Type    Description
========= ======= =================
jobId     Integer The ID of the Job
========= ======= =================

Return: ``true`` if the Job was deleted successfully, ``false`` otherwise
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

.. _schedulergetjob:

Scheduler.getJob
^^^^^^^^^^^^^^^^

Get the JobData for the job with the specified ID.

.. _parameters-3:

Parameters
''''''''''

========= ======= =================
Parameter Type    Description
========= ======= =================
jobId     Integer The ID of the Job
========= ======= =================

.. _return-a-jobdata-object:

Return: a ``JobData`` object.
'''''''''''''''''''''''''''''

.. _schedulersearchjobs:

Scheduler.searchJobs
^^^^^^^^^^^^^^^^^^^^

Get a JobPageData object containing "shallow" JobData objects. These JobData objects do not contain ``jobParameters`` and cannot directly be used to execute jobs via the ``runNow()`` method. However, the job ID can be used to obtain a full ``JobData`` object suitable for execution directly by the ``runNow()`` method.

.. _parameters-4:

Parameters
''''''''''

========== =========== =========================================================================================================
Parameter  Type        Description
========== =========== =========================================================================================================
pageData   JSON Object A ``JobPageData`` object specifying the starting *offset* and *pageSize*.
networks   Array       An array of managed network names to search for jobs in.
sortColumn String      A string indicating the ``JobData`` object attribute the results should be sorted by, *null* for default.
descending Boolean     A boolean flag indicating whether results should be sorted in descending or ascending order.
========== =========== =========================================================================================================

Return: a ``JobPageData`` object containing search results
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

.. raw:: html

   <p class="vspacer"></p>

Scheduler Objects
~~~~~~~~~~~~~~~~~

JobData
^^^^^^^

=============== ======= ==============================================================================================
Field           Type    Description
=============== ======= ==============================================================================================
jobId           Integer The job ID (read-only)
jobName         String  The name of the job
description     String  The description of the job
managedNetworks Array   An array of managed network names this job set is available in
jobType         String  One of the pre-defined NetLD job types (see below)
jobParameters   Map     A map (hash) of job parameter name/value pairs that are specific to each *jobType* (see below)
isAccessLimited Boolean ``true`` if the caller has limited visibility to the networks defined for this job (read-only)
isGlobal        Boolean ``true`` if the specified job is a "global" (aka system) job (read-only)
=============== ======= ==============================================================================================

JobPageData
^^^^^^^^^^^

======== ======= ===================================================================================================================================================================
Field    Type    Description
======== ======= ===================================================================================================================================================================
offset   Integer The starting offset in the results to begin retrieving pageSize number of ``JobData`` objects.
pageSize Integer The maximum number of ``JobData`` objects to retrieve in a single method call.
total    Integer This value is set and retrieved from the server when an offset of zero (0) is passed. This indicates the total number of ``JobData`` objects available. (read-only)
jobData  Array   An array of ``JobData`` objects
======== ======= ===================================================================================================================================================================

ExecutionData
^^^^^^^^^^^^^

=============== ============== ==================================================================================
Field           Type           Description
=============== ============== ==================================================================================
id              Integer        The execution ID
jobName         String         The name of the job
managedNetworks Array          An array of managed network names the job was associated with
executor        String         The user name of the user who executed the job
startTime       64-bit Integer The start time of the job as a Unix epoch value
endTime         64-bit Integer The end time of the job as a Unix epoch value
completionState Integer        0=normal, 1=cancelled, 2=misfired (schedule missed)
status          String         One of: "OK", "WARN", "ERROR", "ABORT"
isPartialView   Boolean        ``true`` if the caller has limited visibility to the networks defined for this job
isGlobal        Boolean        ``true`` if the specified job is a "global" (aka system) job
=============== ============== ==================================================================================

Job Types
^^^^^^^^^

====================== ===============================================
Type Name              Type Description
====================== ===============================================
"Discover Devices"     Network device discovery.
"Backup Configuration" Network device configuration backup.
"Telemetry"            Network device neighbor information collection.
"Script Tool Job"      Pre-definied read/write tool execution.
"Bulk Update"          SmartChange execution.
"Report"               Pre-definied report execution.
====================== ===============================================

Job Parameters (per Job Type)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*All* job parameter names and values are UTF-8 strings. Even "boolean" and "integer" values are represented as strings such as *"true"* or *"5432"*.

"Discover Devices"
''''''''''''''''''

================ ====== ==============================================================================================================================================================================
Name             Type   Value Description
================ ====== ==============================================================================================================================================================================
communityStrings String Additional SNMP community string or comma-separated list of strings
boundaryNetworks String Comma-separated list of discovery boundary networks (CIDR)
crawl            String A "boolean" value indicating whether the discovery should use neighbor/peer information to discover additional devices
includeInventory String A "boolean" value indicating whether the discovery should automatically include current inventory devices. This option is only meaningful when "crawl" is also set to *"true"*
addresses        String A comma-separated list of IP address "shapes" to include in the discovery. See below.
================ ====== ==============================================================================================================================================================================
