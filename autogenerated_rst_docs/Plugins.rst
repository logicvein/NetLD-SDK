Plugins
-------

The plugins API provides access to tool job execution results.

**NOTE: This API has significant and incompatible changes in the next major release. The name of this service endpoint is likely to change. You will need to update any scripts that use these APIs.**

Plugin Service Methods
~~~~~~~~~~~~~~~~~~~~~~

Plugins.getExecutionDetails
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Get the list of ``ToolRunDetails``, one per device, for the given scheduler execution ID. *Note that currently only the SmartChange ("bulk update") job contains accessible tool execution records.*

Parameters
''''''''''

+---------------+-----------+-------------------------------------+
| Parameter     | Type      | Description                         |
+===============+===========+=====================================+
| executionId   | Integer   | The execution ID of the tool job.   |
+---------------+-----------+-------------------------------------+

Return: an array of ``ToolRunDetails`` objects or ``null``
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

Plugins Objects
~~~~~~~~~~~~~~~

ToolRunDetails
^^^^^^^^^^^^^^

+------------------+------------------+----------------------------------------------------------------------------------------------------------------------+
| Field            | Type             | Description                                                                                                          |
+==================+==================+======================================================================================================================+
| id               | Integer          | The ID of the tool detail record, used to retrieve the text of the detail from the detail URL endpoint (see below)   |
+------------------+------------------+----------------------------------------------------------------------------------------------------------------------+
| ipAddress        | String           | The IP address of the device of this detail record                                                                   |
+------------------+------------------+----------------------------------------------------------------------------------------------------------------------+
| managedNetwork   | String           | The name of the network in which the device is defined                                                               |
+------------------+------------------+----------------------------------------------------------------------------------------------------------------------+
| executionId      | Integer          | The ID of the job execution                                                                                          |
+------------------+------------------+----------------------------------------------------------------------------------------------------------------------+
| error            | String           | An error string if one exists, or *null*                                                                             |
+------------------+------------------+----------------------------------------------------------------------------------------------------------------------+
| gridData         | String           | A CSV of execution values, one row per device                                                                        |
+------------------+------------------+----------------------------------------------------------------------------------------------------------------------+
| startTime        | 64-bit Integer   | The start time of the job as a Unix epoch value                                                                      |
+------------------+------------------+----------------------------------------------------------------------------------------------------------------------+
| endTime          | 64-bit Integer   | The end time of the job as a Unix epoch value.                                                                       |
+------------------+------------------+----------------------------------------------------------------------------------------------------------------------+

Some tools return all of their data in the ``gridData`` attribute, others contains additional textual output from the device, available from the URL endpoint below.

Execution Detail URL Endpoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Individual output detail for each device in an execution is available through the following URL endpoint:

::

    https://<host>/servlet/pluginDetail?executionId=<executionId>&recordId=<id>

Where ``<host>`` is the NetLD server, ``<executionId>`` is the job execution ID, and ``<id>`` is the individual record ID contained in the `ToolRunDetails <#toolrundetails>`__ record for a specific device.

Typically, the `Plugins.getExecutionDetails <#plugins.getexecutiondetails>`__ API is used to obtain a list of ``ToolRunDetails`` records, and then for each record (one per device) the URL endpoint is accessed to obtain the textual output from the device.

See the Python example scripts in the SDK for example uses.
