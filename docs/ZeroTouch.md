## Zero Touch (including Cisco PnP)

The zerotouch API provides the core functionality of retrieving Zero Touch post-device deployment status.

See the [ZeroTouch Objects](#zerotouch-objects) section for a description of the various objects consumed and returned by these APIs.

#### ZeroTouch.searchHistory
Retrieves an entire ARP table for the given device.

##### Parameters
| Parameter     | Type       | Description                                                                                                        |
|---------------|------------|--------------------------------------------------------------------------------------------------------------------|
| queryString   | String     | A device identifier, including a possibly trailing wildcard character (*), or empty (zero length string) for *all* |
| pageData      | PageData   | A ``PageData`` object defining the offset where retrieval should begin and page size                               |
| sortColumn    | String     | A string indicating the ``ZcHistory`` object attribute the results should be sorted by                             |
| descending    | Boolean    | A boolean flag indicating whether results should be sorted in descending or ascending order                        |

#### Return: A ``PageData`` object

The ``PageData`` object that is returned will contain an attribute called ``histories``, which is an array
of ``ZcHistory`` objects.  If the initial ``offset`` that is passed is zero (0), the returned ``PageData``
object will also contain a populated ``total`` attribute, telling you how many total results are available.
By incrementing the ``offset`` by ``pageSize`` you can retrieve subsequent pages of results.
When ``offset`` + ``pageSize`` is greater than or equal to ``total`` there are no more results available.

#### Sample Request JSON:

```javascript
{
   "jsonrpc": "2.0",
   "method": "ZeroTouch.searchHistory",
   "params": {
       "queryString": "",
       "pageData": {
            "offset": 0,
            "pageSize": 100
       },
       "sortColumn": "statusTime",
       "descending": true
   },
   "id": 1
}
```

#### Sample Response JSON:

```javascript
{
    "jsonrpc": "2.0", 
    "id": 1,
    "result": {
        "offset": 0,
        "pageSize": 100,
        "total": 1,
        "histories": [
            {
                "deploymentId": "zhe9njl3e5g0",
                "deviceIdent": "FNC90934C",
                "address": "192.168.10.143",
                "statusTime": "2020-11-05T13:15:30Z",
                "statusCode": "STATUS_CODE_SUCCESS",
                "lineNumber": 0,
                "templateName": "Cisco 1841",
                "statusMessage": "STATUS_CODE_SUCCESS"
            }
        ]
    }
}
```

<p class="vspacer"></p>

### ZeroTouch Objects

#### ZcHistory
| Field         | Type     | Description                                                                                     |
|---------------|----------|-------------------------------------------------------------------------------------------------|
| deploymentId  | String   | The internal deployment ID used during provisioning                                             |
| deviceIdent   | String   | The identifier (usually serial number) provided by the device requesting provisioning           |
| address       | String   | The IP address where the request originated. Could be the device or an intermediary relay agent |
| statusTime    | Date     | A W3C formatted date/time string (in the UTC timezone)                                          |
| statusCode    | String   | A value from the status code table below                                                        |
| lineNumber    | Integer  | The line number of a configuration line error rejected by the device, or 0                      |
| templateName  | String   | The name of the ZeroTouch template used for provisioning                                        |
| statusMessage | String   | An error message from the device, or one of "STATUS_CODE_SUCCESS" or "STATUS_CODE_FAILURE"      |


##### Status codes (for ```ZcHistory`` *statusCode* above)
| Status Codes          |
|-----------------------|
| NETLD_DEPLOY          |
| NETLD_RECOVERY        |
| NETLD_NO_CONFIG       |
| STATUS_CODE_SUCCESS   |
| STATUS_CODE_FAILURE   |


#### PageData
| Attribute       | Type      | Description                                                                                                                                                                                                                       |
|-----------------|-----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| offset          | Integer   | The starting ```offset``` in the results to begin retrieving ```pageSize``` number of ```Device``` objects.  This value is required when ```PageData``` is used as a parameter.                                                   |
| pageSize        | Integer   | The maximum number of ```Device``` objects to retrieve in a single method call. This value is required when ```PageData``` is used as a parameter.                                                                                |
| total           | Integer   | This value is set and retrieved from the server when an ```offset``` of zero (0) is passed.  This indicates the total number of ``Device`` objects available.   This value is ignored when ```PageData``` is used as a parameter. |
| histories       | Array     | An array of ``ZcHistory`` objects. This value is ignored when ``HistoryPageData`` is used as a parameter and should be empty for wire efficiency.                                                                                 |

<p class="vspacer"></p>
