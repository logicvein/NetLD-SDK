# Palo Alto Operational Collection

Last updated: 2026-08-28

Tested against: Palo Alto Networks VM-Series firewall with PAN-OS 11.2 MIBs

This example monitor set provides operational visibility into a Palo Alto
Networks firewall's security and management roles. It collects HA state,
aggregate and per-VSYS session demand, GlobalProtect gateway capacity,
Panorama connectivity, PAN-OS and security-content versions, and local and
external log-delivery health.

The collection is intended as a starting point. It does not include alert
policies or environment-specific thresholds. Generic CPU, memory, filesystem,
interface, and uptime monitoring are outside its scope.

## Requirements

Before importing the monitor set, confirm that:

- The firewall has been added to the ThirdEye inventory.
- ThirdEye can reach the firewall's SNMP agent, normally over UDP port 161.
- SNMP has been configured on the firewall and the connection path permits
  queries from the ThirdEye server.
- A matching SNMP credential has been assigned to the device in ThirdEye.
  SNMPv3 with authentication and privacy is recommended.
- The Palo Alto Networks enterprise MIB package has been imported into
  ThirdEye.

This example was developed with the PAN-OS 11.2 enterprise MIB package. Other
PAN-OS and MIB versions may also work, but should be validated before the
monitor set is used in production.

### Obtaining the Palo Alto Networks MIBs

Download the enterprise MIB package for the PAN-OS version being monitored
from Palo Alto Networks' Technical Documentation portal:

- [Enterprise SNMP MIB files](https://docs.paloaltonetworks.com/resources/snmp-mib-files)

The PAN-OS 11.2 package used for this example contains:

- `PAN-GLOBAL-REG-MIB.my`
- `PAN-GLOBAL-TC-MIB.my`
- `PAN-PRODUCT-MIB.my`
- `PAN-COMMON-MIB.my`
- `PAN-ENTITY-EXT-MIB.my`
- `PAN-LC-MIB.my`
- `PAN-TRAPS.my`

Import the complete package so that dependencies and textual conventions used
by `PAN-COMMON-MIB` can be resolved.

## Installation

1. Import the Palo Alto Networks enterprise MIB package into ThirdEye.
2. In **Inventory**, use **Tools > SNMP System Info** to verify that ThirdEye
   can query each target firewall.
3. Go to **Monitors > Sets** and import the monitor-set file supplied with this
   example.
4. Assign **Palo Alto - Operational Collection** to the appropriate firewalls.
5. Wait at least fifteen minutes so every monitor has had a collection
   opportunity, then confirm that current data is present for the applicable
   monitors.

Automatic assignment to newly discovered devices is disabled in the example.
Review the set before enabling automatic assignment in your environment.

## Included monitors

The set contains eleven SNMP monitors. Operational state is generally
collected every minute, log storage every five minutes, and software and
security-content versions every fifteen minutes.

### HA State — 1 minute

- `panSysHAState`
- `panSysHAPeerState`
- `panSysHAMode`

### Session Demand and Capacity — 1 minute

Collects aggregate session utilization, capacity, protocol mix, SSL proxy
usage, and new sessions per second:

- `panSessionUtilization`
- `panSessionMax`
- `panSessionActive`
- `panSessionActiveTcp`
- `panSessionActiveUdp`
- `panSessionActiveICMP`
- `panSessionActiveSslProxy`
- `panSessionSslProxyUtilization`
- `panSessionCps`

### VSYS Session Capacity — 1 minute

Collects session utilization, limits, and connection rates by virtual system
from `PAN-COMMON-MIB::panVsysTable`:

- `panVsysName`
- `panVsysId`
- `panVsysSessionUtilizationPct`
- `panVsysActiveSessions`
- `panVsysMaxSessions`
- `panVsysActiveTcpCps`
- `panVsysActiveUdpCps`
- `panVsysActiveOtherIpCps`

A zero VSYS utilization or maximum can mean that a per-VSYS session limit is
not configured; it must not automatically be interpreted as zero device
capacity.

### GlobalProtect Gateway Capacity — 1 minute

- `panGPGWUtilizationPct`
- `panGPGWUtilizationMaxTunnels`
- `panGPGWUtilizationActiveTunnels`

### Panorama Connectivity and Admin Sessions — 1 minute

- `panMgmtPanoramaConnected`
- `panMgmtPanorama2Connected`
- `panMgmtNumAdminSessions`

### PAN-OS Software Version — 15 minutes

- `panSysSwVersion`

### Security Content Versions — 15 minutes

- `panSysAppVersion`
- `panSysAppReleaseDate`
- `panSysAvVersion`
- `panSysAvReleaseDate`
- `panSysThreatVersion`
- `panSysThreatReleaseDate`
- `panSysUrlFilteringVersion`
- `panSysUrlFilteringDatabase`
- `panSysWildfireVersion`
- `panSysWfReleaseDate`
- `panSysGlobalProtectClientVersion`
- `panSysOpswatDatafileVersion`

Values such as `0`, `0.0.0`, or `unknown` can mean that a package is not
installed. Distinguish those sentinel values from an installed package that is
stale before defining alerts.

### Log Delivery Health — 1 minute

Collects incoming and written log rates plus aggregate external-forwarding
counts, drops, and send errors:

- `panDeviceIncomingLogRate`
- `panDeviceWriteLogRate`
- `panDeviceLoggingExtFwdCount`
- `panDeviceLoggingExtFwdQueueDrop`
- `panDeviceLoggingExtFwdStatsSendErr`

### External Log Forwarding Queues — 1 minute

Collects enqueue, send, drop, queue-depth, and recent send-rate values by
external log type from
`PAN-COMMON-MIB::panDeviceLoggingExtFwdStatsTable`:

- `panDeviceLoggingExtFwdStatsTableType`
- `panDeviceLoggingExtFwdStatsTableEnqueueCount`
- `panDeviceLoggingExtFwdStatsTableSendCount`
- `panDeviceLoggingExtFwdStatsTableDropCount`
- `panDeviceLoggingExtFwdStatsTableQueueDepth`
- `panDeviceLoggingExtFwdStatsTable1minAvgSendRate`

### Log Collector Connections — 1 minute

Collects connection type, address, hostname, and status from
`PAN-COMMON-MIB::panDeviceLoggingCollectorConnectionTable`:

- `panDeviceLoggingCollectorConnectionType`
- `panDeviceLoggingCollectorConnectionIP`
- `panDeviceLoggingCollectorConnectionHostname`
- `panDeviceLoggingCollectorConnectionStatus`

### Log Storage and Retention — 5 minutes

Collects disk use, retention, and quota by log type from
`PAN-COMMON-MIB::panDeviceLoggingLogUsageTable`:

- `panDeviceLoggingLogUsageLogType`
- `panDeviceLoggingDiskUsageDiskSpace`
- `panDeviceLoggingDiskUsageRetention`
- `panDeviceLoggingDiskQuotaPct`
- `panDeviceLoggingDiskQuota`

This is log-database capacity and retention monitoring, not a replacement for
generic filesystem monitoring.

## Expected variations

Some monitors return data only when the corresponding firewall feature is
configured:

- HA state depends on an HA configuration and peer.
- GlobalProtect metrics depend on configured gateways.
- Panorama connectivity values depend on Panorama management configuration.
- Log-forwarding queues and collector connections depend on external
  forwarding and collector configuration.
- Per-VSYS values depend on the appliance's virtual-system configuration and
  any configured limits.

An empty feature-specific table does not necessarily indicate a collection
failure. First confirm whether that feature is configured and active on the
target firewall.

## Validation

To run the **SNMP System Info** tool, open **Inventory**, select the target
firewall, open **Tools**, and select **SNMP System Info**. ThirdEye queries the
device using its assigned SNMP credential. A successful test returns basic
system information, including the system description and uptime, rather than
an SNMP timeout or authentication error.

After installation:

1. Run **SNMP System Info** for every assigned firewall and confirm that it
   succeeds.
2. Confirm that the one-minute scalar monitors have current samples.
3. Wait at least fifteen minutes and confirm that the software and content
   monitors have had a collection opportunity.
4. Verify that each applicable table returns the expected VSYS instances,
   gateways, forwarding queues, and collector connections.
5. Compare HA, Panorama, GlobalProtect, session, and logging values with the
   PAN-OS web interface before creating alert thresholds.

## Limitations

- The example performs collection only; it does not install alert policies,
  notification destinations, or incident workflows.
- Feature-specific tables can be empty on otherwise healthy firewalls.
- Many logging values are cumulative counters. Alerting should use an
  appropriate rate or change over time where supported.
- State strings, version formats, sentinel values, and table availability can
  vary by PAN-OS and MIB version. Validate their meaning before defining
  alerts.
- The example does not contain SNMP usernames, authentication secrets, privacy
  secrets, device addresses, or other environment-specific credentials.

## Troubleshooting

If no data is collected:

1. Run **Inventory > Tools > SNMP System Info** against the device.
2. Confirm network reachability from ThirdEye to UDP port 161 on the firewall.
3. Verify the firewall's SNMP configuration and confirm that the connection
   path permits queries from the ThirdEye server.
4. Verify that the matching SNMP credential is assigned in ThirdEye.
5. Confirm that the complete Palo Alto Networks enterprise MIB package is
   present in ThirdEye.
6. Wait for the applicable collection interval after making a correction.

If scalar metrics work but a table monitor is empty, confirm that the
corresponding PAN-OS feature is configured before treating the result as an
error.
