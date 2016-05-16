## Scheduler

The scheduler API provides access to job management, scheduling and execution.  Job types include tools, configuration backup,
Smart Changes, and reports.

## Scheduler Service Methods

### ``Scheduler.runNow``
Execute a job defined by the specified ``JobData``.
##### Parameters
| Parameter | Type    | Description |
| --------- | ------- | ----------- |
| jobData   | JSON Object | A ``JobData`` object |

##### Return: an ``ExecutionData`` object.

<p class="vspacer"></p>

### ``Scheduler.saveJob``
Save (or replace) the job defined by the specified ``JobData``.
##### Parameters
| Parameter | Type         | Description |
| --------- | ------------ | ----------- |
| jobData   | JSON Object | A ``JobData`` object |

##### Return: the ``JobData`` object with ``jobId`` property populated.

<p class="vspacer"></p>

### ``Scheduler.deleteJob``
Get the policy definition by ID.
##### Parameters
| Parameter | Type    | Description |
| --------- | ------- | ----------- |
| jobId     | Integer | The ID of the Job |

##### Return: ``true`` if the Job was deleted successfully, ``false`` otherwise

<p class="vspacer"></p>

### ``Scheduler.getJob``
Get the list of current violations for a given device.
##### Parameters
| Parameter | Type         | Description |
| --------- | ------------ | ----------- |
| jobId     | Integer      | The ID of the Job |

##### Return: a ``JobData`` object.

<p class="vspacer"></p>

### ``Scheduler.searchJobs``
Get the list of current violations for a given policy.
##### Parameters
| Parameter | Type    | Description |
| --------- | ------- | ----------- |
| pageData  | JSON Object  | A ``JobPageData`` object specifying the starting *offset* and *pageSize*. |
| networks  | Array        | An array of managed network names to search for jobs in. |
| sortColumn  | UTF-8 String | A string indicating the ``JobData`` object attribute the results should be sorted by (*null* for default). |
| descending  | Boolean | A boolean flag indicating whether results should be sorted in descending or ascending order. |

##### Return: an array of ```Violation``` objects

<p class="vspacer"></p>

## Scheduler Objects

### JobData
| Field           | Type          | Description      |
| --------------- | ------------- | --------------   |
| jobId           | Integer       | The job's ID (read-only) |
| jobName         | UTF-8 String  | The name of the job |
| description     | UTF-8 String  | The description of the job |
| managedNetworks | Array         | An array of managed network names this job set is available in |
| jobType         | UTF-8 String  | One of the pre-defined NetLD job types (see below) |
| jobParameters   | Map           | A map (hash) of job parameter name/value pairs that are specific to each *jobType* (see below) |
| isAccessLimited | Boolean       | ``true`` if the caller has limited visibility to the networks defined for this job (read-only) |
| isGlobal        | Boolean       | ``true`` if the specified job is a "global" (aka system) job (read-only) |

### JobPageData
| Field            | Type         | Description      |
| ---------------- | ------------ | --------------   |
| offset           | Integer      | The starting offset in the results to begin retrieving pageSize number of ``JobData`` objects. |
| pageSize         | Integer      | The maximum number of ``JobData`` objects to retrieve in a single method call. |
| total            | Integer      | This value is set and retrieved from the server when an offset of zero (0) is passed. This indicates the total number of ``JobData`` objects available. (read-only) |
| jobData          | Array        | An array of ``JobData`` objects |

### Policy
| Field            | Type         | Description      |
| ---------------- | ------------ | --------------   |
| policyId         | Integer      | The policy's ID |
| policyName       | UTF-8 String | The name of the policy |
| network          | UTF-8 String | The managed network the policy is in |
| adapterId        | UTF-8 String | The Adapter ID of the device |
| configPath       | UTF-8 String | The device configuration this policy applies to |
| resolutionScheme | UTF-8 String | A single scheme name or comma-separated list of scheme names |
| resolutionData   | UTF-8 String | The query associated with the scheme(s) specified |

----------------------------------------------------------------------------------

## Job Types
| Type Name              | Type Description     |
| ---------------------- | -------------------  |
| "Discover Devices"     | Network device discovery. |
| "Backup Configuration" | Network device configuration backup. |
| "Telemetry"            | Network device neighbor information collection. |
| "Script Tool Job"      | Pre-definied read/write tool execution. |
| "Bulk Update"          | SmartChange execution. |
| "Report"               | Pre-definied report execution. |

## Job Parameters (per Job Type)

*All* job parameter names and values are UTF-8 strings.  Even "boolean" and "integer" values are represented as strings such as *"true"* or *"5432"*.

### "Discover Devices"
| Name             | Type           | Value Description      |
| ---------------- | -------------- | --------------------   |
| communityStrings | UTF-8 String   | Additional SNMP community string or comma-separated list of strings |
| boundaryNetworks | UTF-8 String   | Comma-separated list of discovery boundary networks (CIDR) |
| crawl            | UTF-8 String   | A "boolean" value indicating whether the discovery should use neighbor/peer information to discover additional devices |
| includeInventory | UTF-8 String   | A "boolean" value indicating whether the discovery should automatically include current inventory devices.  This option is only meaningful when "crawl" is also set to *"true"* |
| addresses        | UTF-8 String   | A comma-separated list of IP address "shapes" to include in the discovery.  See below. |

