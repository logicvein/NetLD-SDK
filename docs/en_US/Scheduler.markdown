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
| policyId  | Integer | The ID of the desired violations' policy |

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
| isAccessLimited | Boolean       | ``true`` if the caller has limited visibility to the networks defined for this job (read-only) |
| isGlobal        | Boolean       | ``true`` if the specified job is a "global" (aka system) job (read-only) |

### PolicyInfo
| Field            | Type         | Description      |
| ---------------- | ------------ | --------------   |
| policyId         | Integer      | The policy's ID |
| policyName       | UTF-8 String | The name of the policy |
| network          | UTF-8 String | The managed network the policy is in |
| enabled          | Boolean      | A boolean flag indicating whether or not this policy is enabled |
| coveredDevice    | Integer      | The number of devices covered by this policy
| violatingDevices | Integer      | The number of devices in violation of this policy |

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

### Violation
| Field     | Type         | Description      |
| --------- | ------------ | --------------   |
| policyId  | Integer      | The ID of the Policy in violation |
| ruleSetId | Integer      | The ID of the RuleSet in violation |
| ipAddress | UTF-8 String | The IP Address of the device in violation |
| network   | UTF-8 String | The managed network of the device in violation |
| message   | UTF-8 String | The violation message |
| severity  | Integer      | The violation severity. 1 for WARNING, 2 for ERROR |
