Compliance
----------

The compliance API provides access to compliance policies, rules, and
violation information.

Compliance Service Methods
~~~~~~~~~~~~~~~~~~~~~~~~~~

``Compliance.getRuleSet``
^^^^^^^^^^^^^^^^^^^^^^^^^

Get the compliance ruleset for the given ID

Parameters
''''''''''

+-------------+-----------+----------------------------------------+
| Parameter   | Type      | Description                            |
+=============+===========+========================================+
| ruleSetId   | Integer   | The ID of the desired RuleSet object   |
+-------------+-----------+----------------------------------------+

Return: the ``RuleSet`` object or ``null``
''''''''''''''''''''''''''''''''''''''''''

.. raw:: html

   <p class="vspacer">

.. raw:: html

   </p>

``Compliance.getPolicies``
^^^^^^^^^^^^^^^^^^^^^^^^^^

Get the list of policies in a given managed networks.

Parameters
''''''''''

+-------------+----------------+-----------------------+
| Parameter   | Type           | Description           |
+=============+================+=======================+
| network     | UTF-8 String   | The managed network   |
+-------------+----------------+-----------------------+

Return: an array of ``PolicyInfo`` objects
''''''''''''''''''''''''''''''''''''''''''

.. raw:: html

   <p class="vspacer">

.. raw:: html

   </p>

``Compliance.getPolicy``
^^^^^^^^^^^^^^^^^^^^^^^^

Get the policy definition by ID.

Parameters
''''''''''

+-------------+-----------+--------------------------------+
| Parameter   | Type      | Description                    |
+=============+===========+================================+
| policyId    | Integer   | The ID of the desired policy   |
+-------------+-----------+--------------------------------+

Return: a ``Policy`` object or ``null``
'''''''''''''''''''''''''''''''''''''''

.. raw:: html

   <p class="vspacer">

.. raw:: html

   </p>

``Compliance.getViolationsForDevice``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Get the list of current violations for a given device.

Parameters
''''''''''

+-------------+----------------+-------------------------------------+
| Parameter   | Type           | Description                         |
+=============+================+=====================================+
| network     | UTF-8 String   | The managed network of the device   |
+-------------+----------------+-------------------------------------+
| ipAddress   | UTF-8 String   | The IP address of the device        |
+-------------+----------------+-------------------------------------+

Return: an array of ``Violation`` objects
'''''''''''''''''''''''''''''''''''''''''

.. raw:: html

   <p class="vspacer">

.. raw:: html

   </p>

``Compliance.getViolationsForPolicy``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Get the list of current violations for a given policy.

Parameters
''''''''''

+-------------+-----------+-------------------------------------------+
| Parameter   | Type      | Description                               |
+=============+===========+===========================================+
| policyId    | Integer   | The ID of the desired violations policy   |
+-------------+-----------+-------------------------------------------+

Return: an array of ``Violation`` objects
'''''''''''''''''''''''''''''''''''''''''

.. raw:: html

   <p class="vspacer">

.. raw:: html

   </p>

Compliance Objects
~~~~~~~~~~~~~~~~~~

RuleSet
^^^^^^^

+----------------+----------------+-----------------+
| Field          | Type           | Description     |
+================+================+=================+
| ruleSetId      | Integer        | The rule set ID |
+----------------+----------------+-----------------+
| ruleSetName    | UTF-8 String   | The name of the |
|                |                | rule set        |
+----------------+----------------+-----------------+
| adapterId      | UTF-8 String   | The Adapter ID  |
|                |                | of the device   |
+----------------+----------------+-----------------+
| configPath     | UTF-8 String   | The device      |
|                |                | configuration   |
|                |                | this rule       |
|                |                | applies to      |
+----------------+----------------+-----------------+
| ruleSetXml     | UTF-8 String   | The rule set    |
|                |                | definition      |
+----------------+----------------+-----------------+
| networks       | Array          | An array of     |
|                |                | managed         |
|                |                | networks this   |
|                |                | rule set is     |
|                |                | available for   |
+----------------+----------------+-----------------+
| readOnly       | Boolean        | A boolean flag  |
|                |                | indicating      |
|                |                | whether or not  |
|                |                | this rule set   |
|                |                | is editable     |
+----------------+----------------+-----------------+

PolicyInfo
^^^^^^^^^^

+-------------------+---------------+-----------------+
| Field             | Type          | Description     |
+===================+===============+=================+
| policyId          | Integer       | The policy's ID |
+-------------------+---------------+-----------------+
| policyName        | UTF-8 String  | The name of the |
|                   |               | policy          |
+-------------------+---------------+-----------------+
| network           | UTF-8 String  | The managed     |
|                   |               | network the     |
|                   |               | policy is in    |
+-------------------+---------------+-----------------+
| enabled           | Boolean       | A boolean flag  |
|                   |               | indicating      |
|                   |               | whether or not  |
|                   |               | this policy is  |
|                   |               | enabled         |
+-------------------+---------------+-----------------+
| coveredDevice     | Integer       | The number of   |
|                   |               | devices covered |
|                   |               | by this policy  |
+-------------------+---------------+-----------------+
| violatingDevices  | Integer       | The number of   |
|                   |               | devices in      |
|                   |               | violation of    |
|                   |               | this policy     |
+-------------------+---------------+-----------------+

Policy
^^^^^^

+-------------------+---------------+-----------------+
| Field             | Type          | Description     |
+===================+===============+=================+
| policyId          | Integer       | The policy's ID |
+-------------------+---------------+-----------------+
| policyName        | UTF-8 String  | The name of the |
|                   |               | policy          |
+-------------------+---------------+-----------------+
| network           | UTF-8 String  | The managed     |
|                   |               | network the     |
|                   |               | policy is in    |
+-------------------+---------------+-----------------+
| adapterId         | UTF-8 String  | The Adapter ID  |
|                   |               | of the device   |
+-------------------+---------------+-----------------+
| configPath        | UTF-8 String  | The device      |
|                   |               | configuration   |
|                   |               | this policy     |
|                   |               | applies to      |
+-------------------+---------------+-----------------+
| resolutionScheme  | UTF-8 String  | A single scheme |
|                   |               | name or         |
|                   |               | comma-separated |
|                   |               | list of scheme  |
|                   |               | names           |
+-------------------+---------------+-----------------+
| resolutionData    | UTF-8 String  | The query       |
|                   |               | associated with |
|                   |               | the scheme(s)   |
|                   |               | specified       |
+-------------------+---------------+-----------------+

Violation
^^^^^^^^^

+-------------+----------------+------------------------------------------------------+
| Field       | Type           | Description                                          |
+=============+================+======================================================+
| policyId    | Integer        | The ID of the Policy in violation                    |
+-------------+----------------+------------------------------------------------------+
| ruleSetId   | Integer        | The ID of the RuleSet in violation                   |
+-------------+----------------+------------------------------------------------------+
| ipAddress   | UTF-8 String   | The IP Address of the device in violation            |
+-------------+----------------+------------------------------------------------------+
| network     | UTF-8 String   | The managed network of the device in violation       |
+-------------+----------------+------------------------------------------------------+
| message     | UTF-8 String   | The violation message                                |
+-------------+----------------+------------------------------------------------------+
| severity    | Integer        | The violation severity. 1 for WARNING, 2 for ERROR   |
+-------------+----------------+------------------------------------------------------+
