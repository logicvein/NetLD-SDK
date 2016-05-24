Compliance
----------

The compliance API provides access to compliance policies, rules, and violation information.

**NOTE: This API has significant and incompatible changes in the next major release. You will need to update any scripts that use these APIs.**

.. raw:: html

   <hr>

Compliance.getRuleSet
^^^^^^^^^^^^^^^^^^^^^

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

   <hr>

Compliance.getPolicies
^^^^^^^^^^^^^^^^^^^^^^

Get the list of policies in a given managed networks.

Parameters
''''''''''

+-------------+----------+-----------------------+
| Parameter   | Type     | Description           |
+=============+==========+=======================+
| network     | String   | The managed network   |
+-------------+----------+-----------------------+

Return: an array of ``PolicyInfo`` objects
''''''''''''''''''''''''''''''''''''''''''

.. raw:: html

   <hr>

Compliance.getPolicy
^^^^^^^^^^^^^^^^^^^^

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

   <hr>

Compliance.getViolationsForDevice
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Get the list of current violations for a given device.

Parameters
''''''''''

+-------------+----------+-------------------------------------+
| Parameter   | Type     | Description                         |
+=============+==========+=====================================+
| network     | String   | The managed network of the device   |
+-------------+----------+-------------------------------------+
| ipAddress   | String   | The IP address of the device        |
+-------------+----------+-------------------------------------+

Return: an array of ``Violation`` objects
'''''''''''''''''''''''''''''''''''''''''

.. raw:: html

   <hr>

Compliance.getViolationsForPolicy
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

   <hr>

Compliance Objects
~~~~~~~~~~~~~~~~~~

RuleSet
^^^^^^^

+---------------+-----------+----------------------------------------------------------------------+
| Field         | Type      | Description                                                          |
+===============+===========+======================================================================+
| ruleSetId     | Integer   | The rule set ID                                                      |
+---------------+-----------+----------------------------------------------------------------------+
| ruleSetName   | String    | The name of the rule set                                             |
+---------------+-----------+----------------------------------------------------------------------+
| adapterId     | String    | The Adapter ID of the device                                         |
+---------------+-----------+----------------------------------------------------------------------+
| configPath    | String    | The device configuration this rule applies to                        |
+---------------+-----------+----------------------------------------------------------------------+
| ruleSetXml    | String    | The rule set definition                                              |
+---------------+-----------+----------------------------------------------------------------------+
| networks      | Array     | An array of managed networks this rule set is available for          |
+---------------+-----------+----------------------------------------------------------------------+
| readOnly      | Boolean   | A boolean flag indicating whether or not this rule set is editable   |
+---------------+-----------+----------------------------------------------------------------------+

PolicyInfo
^^^^^^^^^^

+--------------------+-----------+-------------------------------------------------------------------+
| Field              | Type      | Description                                                       |
+====================+===========+===================================================================+
| policyId           | Integer   | The policy's ID                                                   |
+--------------------+-----------+-------------------------------------------------------------------+
| policyName         | String    | The name of the policy                                            |
+--------------------+-----------+-------------------------------------------------------------------+
| network            | String    | The managed network the policy is in                              |
+--------------------+-----------+-------------------------------------------------------------------+
| enabled            | Boolean   | A boolean flag indicating whether or not this policy is enabled   |
+--------------------+-----------+-------------------------------------------------------------------+
| coveredDevice      | Integer   | The number of devices covered by this policy                      |
+--------------------+-----------+-------------------------------------------------------------------+
| violatingDevices   | Integer   | The number of devices in violation of this policy                 |
+--------------------+-----------+-------------------------------------------------------------------+

Policy
^^^^^^

+--------------------+-----------+----------------------------------------------------------------+
| Field              | Type      | Description                                                    |
+====================+===========+================================================================+
| policyId           | Integer   | The policy's ID                                                |
+--------------------+-----------+----------------------------------------------------------------+
| policyName         | String    | The name of the policy                                         |
+--------------------+-----------+----------------------------------------------------------------+
| network            | String    | The managed network the policy is in                           |
+--------------------+-----------+----------------------------------------------------------------+
| adapterId          | String    | The Adapter ID of the device                                   |
+--------------------+-----------+----------------------------------------------------------------+
| configPath         | String    | The device configuration this policy applies to                |
+--------------------+-----------+----------------------------------------------------------------+
| resolutionScheme   | String    | A single scheme name or comma-separated list of scheme names   |
+--------------------+-----------+----------------------------------------------------------------+
| resolutionData     | String    | The query associated with the scheme(s) specified              |
+--------------------+-----------+----------------------------------------------------------------+

Violation
^^^^^^^^^

+-------------+-----------+------------------------------------------------------+
| Field       | Type      | Description                                          |
+=============+===========+======================================================+
| policyId    | Integer   | The ID of the Policy in violation                    |
+-------------+-----------+------------------------------------------------------+
| ruleSetId   | Integer   | The ID of the RuleSet in violation                   |
+-------------+-----------+------------------------------------------------------+
| ipAddress   | String    | The IP Address of the device in violation            |
+-------------+-----------+------------------------------------------------------+
| network     | String    | The managed network of the device in violation       |
+-------------+-----------+------------------------------------------------------+
| message     | String    | The violation message                                |
+-------------+-----------+------------------------------------------------------+
| severity    | Integer   | The violation severity. 1 for WARNING, 2 for ERROR   |
+-------------+-----------+------------------------------------------------------+
