#### JSON-RPC
This documentation provides technical details of the NetLD/ThirdEye integration API.  The NetLD/ThirdEye server exposes a JSON-RPC^1^  2.0 API over HTTPS for language neutral integration from external systems. There are many JSON-RPC 2.0 client libraries available for all major languages^2^.  See the *Examples* directory for sample scripts in various languages.

The use of JSON-RPC means that the underlying data sent to or received from the server is in JSON (JavaScript Object Notation) format.  All strings are encoded using UTF-8 encoding, no other encodings are supported.

The access URL for Net LineDancer is:

https://```server```/rest?j_username=```username```&amp;j_password=```password```

Where ```server```, ```username```, and ```password``` are values correct for your installation.

All JSON-RPC requests are performed using the **POST** method. If you hit the URL using the GET method, no operation will be performed, but you will get an "OK" message if the credentials are valid.

The API documentation shows examples of "raw" JSON requests, but it is recommended that you use JSON-RPC libraries appropriate for your language of choice, which will handle the JSON generation for you.

^1^ [http://www.jsonrpc.org/specification](http://www.jsonrpc.org/specification) <br/>
^2^ [http://en.wikipedia.org/wiki/JSON-RPC](http://en.wikipedia.org/wiki/JSON-RPC#Implementations) <br/>


<p>
