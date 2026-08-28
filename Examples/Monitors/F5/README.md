# F5 BIG-IP Operational Collection

Last updated: 2026-08-28

Tested against: F5 BIG-IP Virtual Edition 21.1.0.1

This example monitor set provides baseline operational visibility for F5
BIG-IP appliances. It collects appliance resource usage, high-availability and
configuration-sync state, traffic-group ownership, and the status of virtual
servers, pools, and pool members.

The collection is intended as a starting point. It does not include alert
policies or environment-specific thresholds.

## Requirements

Before importing the monitor set, confirm that:

- The BIG-IP appliance has been added to the ThirdEye inventory.
- ThirdEye can reach the appliance's SNMP agent, normally over UDP port 161.
- The BIG-IP SNMP allowed-hosts configuration includes the ThirdEye server or
  its monitoring subnet.
- A working SNMP credential has been assigned to the device in ThirdEye.
  SNMPv3 with authentication and privacy is recommended.
- The required F5 MIBs have been imported into ThirdEye.

This example was developed with the F5 MIB package version `21.0.0`. The F5
MIB files are not included with this example and must be obtained from F5.
Other BIG-IP and MIB versions may also work, but should be validated before the
monitor set is used in production.

### Obtaining the F5 MIBs

On a TMOS BIG-IP system, download the enterprise MIB archive directly from the
Configuration utility:

1. Open **About**.
2. Select **Downloads**.
3. Select **Download F5 MIBs (`mibs_f5.tar.gz`)**.

The MIB files are also available on the appliance in
`/usr/share/snmp/mibs`.

On an rSeries or other F5OS-based system, open **System Settings > File
Utilities**, select `mibs` as the base directory, select the MIB archive, and
download it.

For additional information, see F5's documentation for
[downloading enterprise and NET-SNMP MIBs](https://techdocs.f5.com/en-us/bigip-16-0-0/external-monitoring-of-big-ip-systems-implementations/monitoring-big-ip-system-traffic-with-snmp.html).

## Installation

1. Import the required F5 MIBs into ThirdEye.
2. In **Inventory**, use **Tools > SNMP System Info** to verify that ThirdEye
   can query each target appliance.
3. Go to **Monitors > Sets** and import the monitor-set file supplied with this
   example.
4. Assign **F5 BIG-IP - Operational Collection** to the appropriate BIG-IP
   devices.
5. Wait at least one collection interval, then confirm that current data is
   present for the applicable monitors.

Automatic assignment to newly discovered devices is disabled in the example.
Review the set before enabling automatic assignment in your environment.

## Included monitors

All six monitors use SNMP and have a one-minute collection interval.

### F5 BIG-IP - Appliance Baseline — 1 minute

Collects general appliance resource and connection statistics:

- `sysGlobalHostCpuUsageRatio1m`
- `sysGlobalTmmStatTmUsageRatio1m`
- `sysGlobalHostOtherMemTotalKb`
- `sysGlobalHostOtherMemUsedKb`
- `sysGlobalTmmStatMemoryTotalKb`
- `sysGlobalTmmStatMemoryUsedKb`
- `sysGlobalHostSwapTotalKb`
- `sysGlobalHostSwapUsedKb`
- `sysGlobalTmmStatClientCurConns`
- `sysGlobalTmmStatServerCurConns`
- `sysGlobalTmmStatDroppedPackets`
- `sysGlobalTmmStatConnectionMemoryErrors`

The set collects the raw used and total memory values. It does not define
derived memory or swap percentages.

### F5 BIG-IP - HA and Config Sync — 1 minute

Collects device-group synchronization and failover state:

- `sysCmSyncStatusId`
- `sysCmSyncStatusStatus`
- `sysCmSyncStatusSummary`
- `sysCmFailoverStatusId`
- `sysCmFailoverStatusStatus`
- `sysCmFailoverStatusSummary`

### F5 BIG-IP - Traffic Groups — 1 minute

Collects traffic-group ownership and failover status from
`F5-BIGIP-SYSTEM-MIB::sysCmTrafficGroupStatusTable`, including:

- `sysCmTrafficGroupStatusTrafficGroup`
- `sysCmTrafficGroupStatusDeviceName`
- `sysCmTrafficGroupStatusFailoverStatus`

### F5 BIG-IP - Virtual Server Status — 1 minute

Collects virtual-server availability and enabled state from
`F5-BIGIP-LOCAL-MIB::ltmVirtualServTable`, including:

- `ltmVirtualServName`
- `ltmVirtualServAvailabilityState`
- `ltmVirtualServEnabledState`
- `ltmVirtualServStatusReason`

### F5 BIG-IP - Pool Status — 1 minute

Collects pool availability and enabled state from
`F5-BIGIP-LOCAL-MIB::ltmPoolStatusTable`, including:

- `ltmPoolStatusName`
- `ltmPoolStatusAvailState`
- `ltmPoolStatusEnabledState`
- `ltmPoolStatusDetailReason`

### F5 BIG-IP - Pool Member Status — 1 minute

Collects pool-member identity, availability, and enabled state from
`F5-BIGIP-LOCAL-MIB::ltmPoolMbrStatusTable`, including:

- `ltmPoolMbrStatusPoolName`
- `ltmPoolMbrStatusNodeName`
- `ltmPoolMbrStatusAddrType`
- `ltmPoolMbrStatusPort`
- `ltmPoolMbrStatusAvailState`
- `ltmPoolMbrStatusEnabledState`
- `ltmPoolMbrStatusDetailReason`

BIG-IP administrative partitions, such as `/Common`, are preserved in the
fully qualified LTM object names returned by the table monitors.

## Expected variations

Some monitors return data only when the corresponding BIG-IP feature is
configured:

- HA and configuration-sync metrics depend on the appliance's device-service
  clustering configuration.
- Traffic-group data depends on the configured traffic groups.
- Virtual-server, pool, and pool-member tables are empty when those objects do
  not exist on the appliance.

An empty feature-specific table does not necessarily indicate a collection
failure. First confirm whether that feature or object type is configured on the
target appliance.

## Validation

To run the **SNMP System Info** tool, open **Inventory**, select the target
BIG-IP appliance, open **Tools**, and select **SNMP System Info**. ThirdEye
queries the device using its assigned SNMP credential. A successful test
returns basic system information, including the system description and uptime,
rather than an SNMP timeout or authentication error.

After installation:

1. Run **SNMP System Info** for every assigned appliance and confirm that it
   succeeds.
2. Confirm that the Appliance Baseline monitor has a current sample.
3. Verify that each applicable table monitor returns the expected BIG-IP
   objects.
4. Check that HA, synchronization, availability, and enabled-state values match
   the state shown by BIG-IP.
5. Review normal operating values in your environment before creating alert
   thresholds.

## Limitations

- The example performs collection only; it does not install alert policies,
  notification destinations, or incident workflows.
- Thresholds should be defined only after establishing a normal baseline for
  the appliance model, software version, traffic profile, and HA design.
- Availability and enumeration values are reported as supplied by the F5 MIBs.
  Interpret them using the MIB definitions applicable to the BIG-IP version
  being monitored.
- The example does not contain SNMP usernames, authentication secrets, privacy
  secrets, device addresses, or other environment-specific credentials.

## Troubleshooting

If no data is collected:

1. Run **Inventory > Tools > SNMP System Info** against the device.
2. Confirm network reachability from ThirdEye to the appliance's SNMP agent.
3. Check the BIG-IP SNMP allowed-hosts configuration.
4. Verify the assigned SNMP version and credentials.
5. Confirm that the required F5 MIBs are present in ThirdEye.
6. Wait at least one collection interval after making a correction.

If scalar appliance metrics work but a table monitor is empty, confirm that the
corresponding BIG-IP feature and objects are configured before treating the
result as an error.
