## Scheduler

**NOTE: This API has significant and incompatible changes in the next major release.  You will need to update any scripts that use these APIs.**

The scheduler API provides access to job management, scheduling and execution.  Job types include tools, configuration backup, Smart Changes, and reports.

#### Scheduler.runNow
Execute a job defined by the specified ``JobData``.

##### Parameters
| Parameter | Type    | Description |
| --------- | ------- | ----------- |
| jobData   | JSON Object | A ``JobData`` object |

##### Return: an ``ExecutionData`` object.

<hr>

#### Scheduler.addJob
Save (or replace) the job defined by the specified ``JobData``.

##### Parameters
| Parameter | Type         | Description |
| --------- | ------------ | ----------- |
| jobData   | JSON Object  | A ``JobData`` object |
| replace   | boolean      | true if an existing job with the same name replaced, false otherwise |

##### Return: the ``JobData`` object with ``jobId`` property populated.


#### Scheduler.deleteJob
Delete the specified job.

##### Parameters
| Parameter | Type    | Description |
| --------- | ------- | ----------- |
| managedNetwork | String | The name of the network in which the job is defined |
| jobName        | String | The name of the job to delete |

##### Return: ``true`` if the Job was deleted successfully, ``false`` otherwise


#### Scheduler.getJob
Get the ``JobData`` for the specified device.

##### Parameters
| Parameter | Type         | Description |
| --------- | ------------ | ----------- |
| managedNetwork | String | The name of the network in which the job is defined |
| jobName        | String | The name of the job |

##### Return: a ``JobData`` object.

<p class="vspacer"></p>

#### Scheduler.scheduleJob
Create a "trigger" (schedule) for a job.

##### Parameters
| Parameter | Type         | Description |
| --------- | ------------ | ----------- |
| triggerData | JSON Object | The schedule (trigger) definition |

##### Return: an updated ``TriggerData`` object.

<p class="vspacer"></p>

#### Scheduler.unscheduleJob
Delete a "trigger" (schedule) for a job.

##### Parameters
| Parameter | Type         | Description |
| --------- | ------------ | ----------- |
| managedNetwork | String | The name of the network in which the schedule is defined |
| triggerData    | String | The schedule (trigger) name |
| jobName        | String | The name of the job |

##### Return: a boolean, *true* if the trigger was found and deleted


### Scheduler Objects

#### JobData
| Field           | Type          | Description      |
| --------------- | ------------- | --------------   |
| jobName         | String  | The name of the job |
| description     | String  | The description of the job |
| managedNetwork  | String | The name of the network in which the job is defined |
| jobType         | String  | One of the pre-defined NetLD job types (see below) |
| jobParameters   | Map           | A map (hash) of job parameter name/value pairs that are specific to each *jobType* (see below) |

#### TriggerData
| Field           | Type          | Description      |
| --------------- | ------------- | --------------   |
| triggerName         | String  | The name of the schedule (trigger) |
| jobName         | String  | The name of the job |
| jobNetwork      | String  | The name of the network in which the schedule (trigger) is defined |
| timeZone        | String  | The timezone name |
| cronExpression  | String  | The cron expression |

#### ExecutionData
| Field            | Type         | Description      |
| ---------------- | ------------ | --------------   |
| id               | Integer      | The execution ID |
| jobName          | String  | The name of the job |
| managedNetworks  | Array         | An array of managed network names the job was associated with |
| executor         | String  | The user name of the user who executed the job |
| startTime        | 64-bit Integer  | The start time of the job as a Unix epoch value |
| endTime          | 64-bit Integer  | The end time of the job as a Unix epoch value |
| completionState  | Integer      | 0=normal, 1=cancelled, 2=misfired (schedule missed) |
| status           | String | One of: "OK", "WARN", "ERROR", "ABORT" |
| isPartialView    | Boolean       | ``true`` if the caller has limited visibility to the networks defined for this job |
| isGlobal         | Boolean       | ``true`` if the specified job is a "global" (aka system) job |


#### Job Types
| Type Name              | Type Description     |
| ---------------------- | -------------------  |
| "Discover Devices"     | Network device discovery. |
| "Backup Configuration" | Network device configuration backup. |
| "Telemetry"            | Network device neighbor information collection. |
| "Script Tool Job"      | Pre-definied read/write tool execution. |
| "Bulk Update"          | SmartChange execution. |
| "Report"               | Pre-definied report execution. |

#### Job Parameters (per Job Type)

*All* job parameter names and values are UTF-8 strings.  Even "boolean" and "integer" values are represented as strings such as *"true"* or *"5432"*.

##### "Discover Devices"
| Name             | Type           | Value Description      |
| ---------------- | -------------- | --------------------   |
| communityStrings | String   | Additional SNMP community string or comma-separated list of strings |
| boundaryNetworks | String   | Comma-separated list of discovery boundary networks (CIDR) |
| crawl            | String   | A "boolean" value indicating whether the discovery should use neighbor/peer information to discover additional devices |
| includeInventory | String   | A "boolean" value indicating whether the discovery should automatically include current inventory devices.  This option is only meaningful when "crawl" is also set to *"true"* |
| addresses        | String   | A comma-separated list of IP address "shapes" to include in the discovery.  See below. |
