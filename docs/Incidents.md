## Incidents

The incidents API provides the core functionality of searching ThirdEye incidents.

See the [Incident Objects](#incident-objects) section for a description of the various objects consumed and returned by these APIs.

<p></p>

### Incident.search

The ``Incidents.search`` method is the fundemental way of retrieving incidents from the server.  Search supports many criteria, and the criteria can be combined to perform powerful searches.

| Parameter     | Type       | Description                                                                                 |
| ------------- |------------|---------------------------------------------------------------------------------------------|
| pageData      | Object     | A ``PageData`` object defining the offset where retrieval should begin and page size        |
| queries       | Array      | An array of query strings defining the search criteria                                      |
| sortColumn    | String     | A string indicating the ``Incident`` object attribute the results should be sorted by       |
| descending    | Boolean    | A boolean flag indicating whether results should be sorted in descending or ascending order |

Within the ``queries`` array, each query string contains a schema, followed by an equals sign, followed by the value of the search parameter.

Example: [``"severity=CRITICAL"``, ``"hostname=web"``]

| Scheme     | Description                                                                    |
|------------|--------------------------------------------------------------------------------|
| incidentId | The internal ID of the Incident                                                |
| severity   | The severity of the Incident                                                   |
| status     | The status of the Incident                                                     |
| hostname   | The hostname or hostname prefix of a device associated with the Incident       |
| ipAddress  | The IP address, or CIDR mask, of a device(s) associated with the Incident      |
| start      | Search Incidents where the specified value is &gt;= the ``modified`` timestamp |
| end        | Search Incidents where the specified value is &lt;= the ``created`` timestamp  |

#### Return: A ``PageData`` object

The ``PageData`` object that is returned will contain an attribute called ``incidents``, which is an array
of ``Incident`` objects.  If the initial ``offset`` that is passed is zero (0), the returned ``PageData``
object will also contain a populated ``total`` attribute, telling you how many total results are available.
By incrementing the ``offset`` by ``pageSize`` you can retrieve subsequent pages of results.
When ``offset`` + ``pageSize`` is greater than or equal to ``total`` there are no more results available.

#### Sample Request JSON:

```javascript
{
   "jsonrpc": "2.0",
   "method": "Incidents.search",
   "params": {
        "pageData": {
            "offset": 0,
            "pageSize": 100
        },
       "queries": ["severity=CRITICAL", "hostname=web"],
       "sortColumn": "modified",
       "descending": true
   },
   "id": 1
}
```

<p class="vspacer"></p>

### Incident.getIncidentById

The ``Incidents.getIncidentById`` method returns an ``Incident`` object as described below, or ``null`` if the requested Incident does not exist.

| Parameter     | Type       | Description                                                                                 |
| ------------- |------------|---------------------------------------------------------------------------------------------|
| incidentId    | Integer    | The internal ID of the Incident                                                            |

#### Return: An ``Incident`` object or null

<p class="vspacer"></p>

### Incident Objects

#### Incident
| Field      | Type   | Description                                                            |
|------------|--------|------------------------------------------------------------------------|
| incidentId | Int    | The internal Incident ID of the device                                 |
| summary    | String | The generated or edited summary of the Incident                        |
| severity   | String | NONE,DEBUG,INFORMATIONAL,NOTICE,WARNING,ERROR,CRITICAL,ALERT,EMERGENCY |
| priority   | String | LOW,MEDIUM,HIGH                                                        |
| status     | String | OPEN,RESOLVED,WORKING,DEFERRED                                         |
| resolution | String | PENDING,FIXED,EXPECTED,TRANSIENT                                       |
| assignee   | String | The username of the user assigned to the Incident                      |
| clearState | String | NOT_CLEARED,CLEARING,CLEARED                                           |
| created    | Date   | The timestamp of when the Incident was created                         |
| modified   | Date   | The timestamp of when the Incident was last modified                   |
| resolved   | Date   | The timestamp of when the Incident was resolved                        |
| nodes      | Int    | The number of nodes associated with the Incident                       |
| triggers   | Int    | The number of triggers associated with the Incident                    |
| occurrences| Int    | The number of occurrences associated with the Incident                 |

#### PageData
| Attribute | Type          | Description                                                                                                                                                                                                             |
|-----------| ------------- |-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| offset    | Integer       | The starting ```offset``` in the results to begin retrieving ``pageSize`` number of ``Incident`` objects.  This value is required when ``PageData`` is used as a parameter.                                             |
| pageSize  | Integer       | The maximum number of ``Incident`` objects to retrieve in a single method call. This value is required when ``PageData`` is used as a parameter.                                                                        |
| total     | Integer  | This value is set and retrieved from the server when an ``offset`` of zero (0) is passed.  This indicates the total number of ``Incident`` objects available.   This value is ignored when ``PageData`` is used as a parameter. |
| incidents | Array | An array of ``Incident`` objects. This value is ignored when ``PageData`` is used as a parameter.                                                                                                                       |

<p class="vspacer"></p>
