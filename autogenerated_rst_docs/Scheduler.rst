Overview
--------

The scheduler API provides access to job management, scheduling and
execution. Job types include tools, configuration backup, Smart Changes,
and reports.

+--------------------------------------------------------------------------+
| ### Scheduler.runNow Execute a job defined by the specified              |
| ```JobData`` <#jobdata>`__. ##### Parameters \| Parameter \| Type \|     |
| Description \| \| --------- \| ------- \| ----------- \| \| jobData \|   |
| JSON Object \| A ``JobData`` object \| ##### Return: an                  |
| ```ExecutionData`` <#executiondata>`__ object.                           |
+==========================================================================+
| ## Job Types \| Type Name \| Type Description \| \|                      |
| ---------------------- \| ------------------- \| \| "Discover Devices"   |
| \| Network device discovery. \| \| "Backup Configuration" \| Network     |
| device configuration backup. \| \| "Telemetry" \| Network device         |
| neighbor information collection. \| \| "Script Tool Job" \| Pre-definied |
| read/write tool execution. \| \| "Bulk Update" \| SmartChange execution. |
| \| \| "Report" \| Pre-definied report execution. \|                      |
+--------------------------------------------------------------------------+

Job Parameters (per Job Type)
-----------------------------

*All* job parameter names and values are UTF-8 strings. Even "boolean"
and "integer" values are represented as strings such as *"true"* or
*"5432"*.

"Discover Devices"
~~~~~~~~~~~~~~~~~~

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

