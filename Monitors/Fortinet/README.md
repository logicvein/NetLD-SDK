# FortiGate Operational Collection

Last updated: 2026-08-28

Tested against: FortiGate-VM64-KVM running FortiOS 7.6.7

This example monitor set provides operational visibility into the FortiGate's
firewall role. It collects HA and configuration-sync state, VPN service and
tunnel state, firewall-policy activity, session demand and failure signals,
SD-WAN SLA results, log delivery, software and security-content versions, and
FortiGuard contract and update status.

The collection is intended as a starting point. It does not include alert
policies or environment-specific thresholds. Generic CPU, memory, disk,
interface, and uptime monitoring are outside its scope.

## Requirements

Before importing the monitor set, confirm that:

- The FortiGate has been added to the ThirdEye inventory.
- ThirdEye can reach the FortiGate SNMP agent, normally over UDP port 161.
- SNMP administrative access is enabled on the FortiGate interface through
  which ThirdEye connects.
- The FortiGate SNMP community or SNMPv3 user permits queries from the ThirdEye
  server. SNMPv3 with authentication and privacy is recommended.
- A matching SNMP credential has been assigned to the device in ThirdEye.
- `FORTINET-CORE-MIB` and `FORTINET-FORTIGATE-MIB` have been imported into
  ThirdEye.

This example was developed with Fortinet MIB files downloaded from a FortiGate
running FortiOS 7.6.7. Other FortiGate and MIB versions may also work, but
should be validated before the monitor set is used in production.

### Obtaining the Fortinet MIBs

Download both required MIB files directly from the FortiGate GUI:

1. Open **System > SNMP**.
2. Select **Download FortiGate MIB File**.
3. Select **Download Fortinet Core MIB File**.

Both files are required because the FortiGate MIB uses definitions from the
Fortinet Core MIB.

For additional information, see Fortinet's documentation for
[FortiGate MIB files](https://docs.fortinet.com/document/fortigate/7.6.2/administration-guide/608160/mib-files).

## Installation

1. Import `FORTINET-CORE-MIB.mib` and `FORTINET-FORTIGATE-MIB.mib` into
   ThirdEye.
2. In **Inventory**, use **Tools > SNMP System Info** to verify that ThirdEye
   can query each target FortiGate.
3. Go to **Monitors > Sets** and import the monitor-set file supplied with this
   example.
4. Assign **FortiGate - Operational Collection** to the appropriate FortiGate
   devices.
5. Wait at least fifteen minutes so every monitor has had a collection
   opportunity, then confirm that current data is present for the applicable
   monitors.

Automatic assignment to newly discovered devices is disabled in the example.
Review the set before enabling automatic assignment in your environment.

## Included monitors

The set contains fourteen SNMP monitors. Operational state is generally
collected every minute, firewall-policy activity every five minutes, and
software, security-content, and FortiGuard information every fifteen minutes.

### HA Cluster Configuration — 1 minute

Identifies whether HA is configured and whether automatic synchronization is
expected:

- `fgHaSystemMode`
- `fgHaAutoSync`
- `fgHaGroupName`

### HA Member and Config Sync — 1 minute

Collects HA member identity, synchronization state and history, primary-member
identity, and configuration checksums from
`FORTINET-FORTIGATE-MIB::fgHaStatsTable`:

- `fgHaStatsSerial`
- `fgHaStatsHostname`
- `fgHaStatsSyncStatus`
- `fgHaStatsSyncDatimeSucc`
- `fgHaStatsSyncDatimeUnsucc`
- `fgHaStatsGlobalChecksum`
- `fgHaStatsMasterSerial`
- `fgHaStatsAllChecksum`

The monitor retains the older `fgHaStatsMasterSerial` label for the OID that
newer Fortinet MIBs call `fgHaStatsPrimarySerial`.

### IPsec Tunnel State — 1 minute

Collects tunnel identity, peer, lifetime, traffic, status, and VDOM from
`FORTINET-FORTIGATE-MIB::fgVpnTunTable`:

- `fgVpnTunEntPhase1Name`
- `fgVpnTunEntPhase2Name`
- `fgVpnTunEntRemGwyIp`
- `fgVpnTunEntLifeSecs`
- `fgVpnTunEntInOctets`
- `fgVpnTunEntOutOctets`
- `fgVpnTunEntStatus`
- `fgVpnTunEntVdom`

### SSL VPN Service and Capacity — 1 minute

Collects SSL VPN state and active usage relative to configured or licensed
capacity from `FORTINET-FORTIGATE-MIB::fgVpnSslStatsTable`:

- `fgVdEntName`
- `fgVpnSslState`
- `fgVpnSslStatsLoginUsers`
- `fgVpnSslStatsMaxUsers`
- `fgVpnSslStatsActiveWebSessions`
- `fgVpnSslStatsMaxWebSessions`
- `fgVpnSslStatsActiveTunnels`
- `fgVpnSslStatsMaxTunnels`

### Firewall Policy Activity — 5 minutes

Collects policy identifiers, high-capacity traffic counters, and last-used
state from `FORTINET-FORTIGATE-MIB::fgFwPolStatsTable`:

- `fgFwPolID`
- `fgFwPolPktCountHc`
- `fgFwPolByteCountHc`
- `fgFwPolLastUsed`

Policy IDs must be correlated with the FortiGate configuration when presenting
policy names or intent.

### Session Demand — 1 minute

Collects current IPv4 and IPv6 session counts and establishment rates:

- `fgSysSesCount`
- `fgSysSesRate1`
- `fgSysSesRate10`
- `fgSysSesRate30`
- `fgSysSesRate60`
- `fgSysSes6Count`
- `fgSysSes6Rate1`
- `fgSysSes6Rate10`
- `fgSysSes6Rate30`
- `fgSysSes6Rate60`

### Session Failure Signals — 1 minute

Collects indicators of ephemeral-session pressure, collisions, expiry,
synchronization and accept-queue failures, and connections without a listener:

- `fgSIAdvSesEphemeralCount`
- `fgSIAdvSesEphemeralLimit`
- `fgSIAdvSesClashCount`
- `fgSIAdvSesExpCount`
- `fgSIAdvSesSyncQFCount`
- `fgSIAdvSesAcceptQFCount`
- `fgSIAdvSesNoListenerCount`

### Configuration Change State — 1 minute

Collects the configuration serial, checksum, and last-change value:

- `fgConfigSerial`
- `fgConfigChecksum`
- `fgConfigLastChangeTime`

The configuration serial increments when the configuration changes. The
last-change value is relative to system uptime rather than a wall-clock
timestamp.

### Log Delivery Health — 1 minute

Collects sent, relayed, cached, failed, and dropped log counts by destination
from `FORTINET-FORTIGATE-MIB::fgLogDeviceTable`:

- `fgLogDeviceName`
- `fgLogDeviceSentCount`
- `fgLogDeviceRelayedCount`
- `fgLogDeviceCachedCount`
- `fgLogDeviceFailedCount`
- `fgLogDeviceDroppedCount`

### SD-WAN Link SLA — 1 minute

Collects per-member state and recent latency, jitter, loss, bandwidth, and MOS
results from `FORTINET-FORTIGATE-MIB::fgVWLHealthCheckLinkTable`:

- `fgVWLHealthCheckLinkName`
- `fgVWLHealthCheckLinkSeq`
- `fgVWLHealthCheckLinkState`
- `fgVWLHealthCheckLinkLatency`
- `fgVWLHealthCheckLinkJitter`
- `fgVWLHealthCheckLinkPacketLoss`
- `fgVWLHealthCheckLinkVdom`
- `fgVWLHealthCheckLinkIfName`
- `fgVWLHealthCheckLinkUsedBandwidthIn`
- `fgVWLHealthCheckLinkUsedBandwidthOut`
- `fgVWLHealthCheckLinkMOSCodec`
- `fgVWLHealthCheckLinkMOS`

Latency, jitter, and packet loss are reported by FortiGate over its recent
probe window. MOS values are present only when the health check uses that
capability.

### FortiOS Firmware Version — 15 minutes

- `fgSysVersion`

### Security Content Versions — 15 minutes

- `fgSysVersionAv`
- `fgSysVersionIps`
- `fgSysVersionAvEt`
- `fgSysVersionIpsEt`

Firmware and security-content versions are collected separately so a problem
with one branch does not prevent collection of the other.

### FortiGuard Contract Status — 15 minutes

Collects contract descriptions and expiry values from
`FORTINET-FORTIGATE-MIB::fgLicContractTable`:

- `fgLicContractDesc`
- `fgLicContractExpiry`

### FortiGuard Package Update Status — 15 minutes

Collects package version, expiry, update method, and last update-attempt status
from `FORTINET-FORTIGATE-MIB::fgLicVersionTable`:

- `fgLicVersionDesc`
- `fgLicVersionExpiry`
- `fgLicVersionNumber`
- `fgLicVersionUpdTime`
- `fgLicVersionUpdMethod`
- `fgLicVersionTryTime`
- `fgLicVersionTryResult`

Together, the two FortiGuard monitors help distinguish an expired entitlement
from a package-update failure while a contract remains current.

## Expected variations

Some monitors return data only when the corresponding FortiGate feature is
configured:

- HA tables depend on an HA cluster configuration.
- IPsec and SSL VPN tables depend on the corresponding VPN services.
- SD-WAN SLA data depends on configured health checks and member links.
- Log-delivery data depends on configured external log destinations.
- FortiGuard contract and package tables depend on the appliance's licensed
  services.
- The firewall-policy table can include Fortinet's policy-zero `No Session
  Data` placeholder when no eligible policy has session data.

An empty feature-specific table does not necessarily indicate a collection
failure. First confirm whether that feature is configured and active on the
target FortiGate.

## Validation

To run the **SNMP System Info** tool, open **Inventory**, select the target
FortiGate, open **Tools**, and select **SNMP System Info**. ThirdEye queries the
device using its assigned SNMP credential. A successful test returns basic
system information, including the system description and uptime, rather than
an SNMP timeout or authentication error.

After installation:

1. Run **SNMP System Info** for every assigned FortiGate and confirm that it
   succeeds.
2. Confirm that the one-minute scalar monitors have current samples.
3. Wait at least fifteen minutes and confirm that the firmware, content, and
   FortiGuard monitors have had a collection opportunity.
4. Verify that each applicable table returns the expected VDOMs, policies,
   tunnels, cluster members, links, and log destinations.
5. Compare operational states with the FortiGate GUI before creating alert
   thresholds.

## Limitations

- The example performs collection only; it does not install alert policies,
  notification destinations, or incident workflows.
- Feature-specific tables can be empty on otherwise healthy appliances.
- Many traffic, session, log, and failure values are cumulative counters.
  Alerting should use an appropriate rate or change over time where supported.
- Version formats, enumerations, timestamps, and entitlement values can vary by
  FortiOS and MIB version. Validate their meaning before defining alerts.
- The example does not contain SNMP usernames, authentication secrets, privacy
  secrets, device addresses, or other environment-specific credentials.

## Troubleshooting

If no data is collected:

1. Run **Inventory > Tools > SNMP System Info** against the device.
2. Confirm network reachability from ThirdEye to UDP port 161 on the FortiGate.
3. Confirm that SNMP administrative access is enabled on the receiving
   FortiGate interface.
4. Verify that the SNMP user or community permits the ThirdEye server and that
   the matching credential is assigned in ThirdEye.
5. Confirm that both Fortinet MIB files are present in ThirdEye.
6. Wait for the applicable collection interval after making a correction.

If scalar metrics work but a table monitor is empty, confirm that the
corresponding FortiGate feature is configured before treating the result as an
error.
