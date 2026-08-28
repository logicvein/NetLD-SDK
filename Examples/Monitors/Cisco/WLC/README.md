# Cisco Catalyst 9800 WLC Operational Collection

Last updated: 2026-08-28

Tested against: Cisco C9800-CL running IOS XE 17.15.4d

This example monitor set provides operational visibility into the wireless
controller role of a Cisco Catalyst 9800. It collects controller reload state,
joined AP demand, AP inventory and stability, radio state and utilization,
WLAN service state, and configured RADIUS authentication-server state.

The collection is intended as a starting point. It does not include alert
policies or environment-specific thresholds. Generic CPU, memory, storage,
interface, uptime, ping, and configuration-backup monitoring are outside its
scope because ThirdEye already provides conventional monitors for them.

## Requirements

Before importing the monitor set, confirm that:

- The Catalyst 9800 has been added to the ThirdEye inventory.
- ThirdEye can reach the controller's SNMP agent, normally over UDP port 161.
- SNMP is enabled and permits queries from the ThirdEye server. SNMPv3 with
  authentication and privacy is recommended.
- A matching SNMP credential has been assigned to the device in ThirdEye.
- The required Cisco MIB modules are installed in ThirdEye.

The collection uses these modules:

- `AIRESPACE-WIRELESS-MIB`
- `CISCO-LWAPP-AP-MIB`
- `OLD-CISCO-SYSTEM-MIB`

The Cisco MIB files are not included with this example. Cisco states that the
same Catalyst 9800 MIB package applies across the 9800-80, 9800-40, 9800-L,
9800-CL, and Embedded Wireless Controller variants. Obtain the current package
from Cisco and validate it against the controller release before broad use.

### Obtaining the Cisco MIBs

1. Open the [Cisco MIB download site](https://cfnng.cisco.com/mibs).
2. Download the Catalyst 9800 MIB archive with the most recent publication
   date. Cisco notes that the newest archive is identified by its date, not
   necessarily by the highest version-like filename.
3. Extract the archive and import the required modules and their dependencies
   into ThirdEye.

For Cisco's SNMP support guidance, MIB compatibility notes, and OID validation
examples, see
[Monitor Catalyst 9800 WLC via SNMP with OIDs](https://www.cisco.com/c/en/us/support/docs/wireless/catalyst-9800-series-wireless-controllers/217460-monitor-catalyst-9800-wlc-via-snmp-with.html).

## Installation

1. Import the required Cisco MIB modules if they are not already available.
2. In **Inventory**, use **Tools > SNMP System Info** to verify SNMP access to
   each target controller.
3. Go to **Monitors > Sets** and import
   `Cisco Catalyst 9800 WLC - Operational Collection.3em`.
4. Assign **Cisco Catalyst 9800 WLC - Operational Collection** only to the
   intended Catalyst 9800 controllers.
5. Wait at least fifteen minutes so every monitor has had a collection
   opportunity, then review each assigned device under **Inventory > device >
   Monitors**.

Automatic assignment to newly discovered devices is disabled. Review the set
before enabling automatic assignment in any environment.

## Included monitors

The set contains eight SNMP monitors. Wireless operational state is collected
every minute, while the controller's last-reload reason is collected every
fifteen minutes.

### Controller Reload State — 15 minutes

- `whyReload`

The software image and uptime are already available from normal device
inventory and SNMP System Info, so this monitor collects only Cisco's printable
last-reload reason.

### Joined Access Point Demand — 1 minute

- `cLApGlobalAPConnectCount`

This scalar reports the current number of APs joined to the controller.

### Access Point Inventory and State — 1 minute

From `AIRESPACE-WIRELESS-MIB::bsnAPTable`:

- `bsnAPName`
- `bsnApIpAddress`
- `bsnAPLocation`
- `bsnAPModel`
- `bsnAPSerialNumber`
- `bsnAPSoftwareVersion`
- `bsnAPOperationStatus`
- `bsnAPAdminStatus`
- `bsnAPPrimaryMwarName`
- `bsnAPNumOfSlots`

### Access Point Health and Stability — 1 minute

From `CISCO-LWAPP-AP-MIB::cLApTable`:

- `cLApName`
- `cLApUpTime`
- `cLLwappUpTime`
- `cLApLastRebootReason`
- `cLApAdminStatus`
- `cLApAssociatedClientCount`
- `cLApMemoryCurrentUsage`
- `cLApMemoryAverageUsage`
- `cLApCpuCurrentUsage`
- `cLApCpuAverageUsage`
- `cLApConnectCount`
- `cLApAbnormalOfflineCount`
- `cLApActiveClientCount`
- `cLApHeartBeatRspAvgTime`
- `cLApEchoResponseLossCount`

Some Catalyst 9800/AP combinations return `-` for counters they do not
implement. Treat that as unsupported data, not zero.

### Radio State and Capacity — 1 minute

From `AIRESPACE-WIRELESS-MIB::bsnAPIfTable`:

- `bsnAPIfSlotId`
- `bsnAPIfType`
- `bsnAPIfPhyChannelNumber`
- `bsnAPIfPhyTxPowerLevel`
- `bsnAPIfNumberOfVaps`
- `bsnAPIfOperStatus`
- `bsnApIfNoOfUsers`
- `bsnAPIfAdminStatus`

The row index is the AP MAC-address suffix plus radio slot. Client MAC
addresses are not collected.

### Radio Load and Client Quality — 1 minute

From `AIRESPACE-WIRELESS-MIB::bsnAPIfLoadParametersTable`:

- `bsnAPIfLoadRxUtilization`
- `bsnAPIfLoadTxUtilization`
- `bsnAPIfLoadChannelUtilization`
- `bsnAPIfLoadNumOfClients`
- `bsnAPIfPoorSNRClients`

### WLAN Service State — 1 minute

From `AIRESPACE-WIRELESS-MIB::bsnDot11EssTable`:

- `bsnDot11EssIndex`
- `bsnDot11EssSsid`
- `bsnDot11EssAdminStatus`
- `bsnDot11EssRadioPolicy`
- `bsnDot11EssNumberOfMobileStations`
- `bsnDot11EssInterfaceName`
- `bsnDot11EssBroadcastSsid`

On the tested IOS XE release, legacy text fields can display `-` even while the
WLAN's administrative and client-count values are available.

### RADIUS Authentication Server State — 1 minute

From `AIRESPACE-WIRELESS-MIB::bsnRadiusAuthServerTable`:

- `bsnRadiusAuthServerIndex`
- `bsnRadiusAuthServerAddress`
- `bsnRadiusAuthClientServerPortNumber`
- `bsnRadiusAuthServerStatus`
- `bsnRadiusAuthServerRetransmitTimeout`
- `bsnRadiusAuthServerRowStatus`

RADIUS shared secrets and key-wrapping material are deliberately excluded. An
empty result is expected when no RADIUS authentication server is configured.

## Expected variations

- Catalyst 9800 emphasizes streaming telemetry; not every field available in
  older AireOS MIBs is implemented on every IOS XE release.
- AP and radio tables depend on currently joined APs.
- WLAN text fields vary by release even when status and client counts work.
- RADIUS rows depend on configured authentication servers.
- A first broad collection can time out while later scheduled cycles succeed.
  Confirm a repeated failure before changing the package.
- High-availability objects are not included because `CISCO-LWAPP-HA-MIB` was
  not installed in the tested ThirdEye MIB library. Add HA monitoring only after
  importing and validating that module against an HA pair.

## Alerting guidance

The package installs no triggers. Establish a normal baseline first. Good
candidate conditions include an unexpected drop in joined AP count, an AP
administratively enabled but operationally unavailable, sustained channel
utilization, increasing abnormal-offline or echo-loss counters, a WLAN becoming
disabled, and a configured RADIUS server leaving service.

Use changes over time for cumulative counters. Do not alert directly on raw
lifetime totals.

## Validation

To run the **SNMP System Info** tool, open **Inventory**, select the target
controller, open **Tools**, and select **SNMP System Info**. ThirdEye queries
the device using its assigned SNMP credential. A successful test returns basic
system information, including the system description and uptime, rather than
an SNMP timeout or authentication error.

After installation:

1. Run **SNMP System Info** for every assigned controller and confirm that it
   succeeds.
2. Confirm that **Joined Access Point Demand** has a current sample.
3. Verify that the AP inventory, AP health, radio, and WLAN tables return the
   expected controller objects.
4. Compare AP state, radio state, client counts, WLAN state, and configured
   RADIUS servers with the Catalyst 9800 interface before creating thresholds.
5. Wait through the fifteen-minute interval and verify the controller reload
   state collection.
6. Treat `-` or an empty feature-specific table as a compatibility or
   configuration check, not automatically as a collection failure.

## Limitations

- The example performs collection only; it installs no alert policies,
  notification destinations, or incident workflows.
- Catalyst 9800 prioritizes streaming telemetry, and some legacy AireOS MIB
  objects are not implemented on every IOS XE and AP combination.
- The set does not collect client MAC addresses, usernames, per-client traffic,
  WLAN pre-shared keys, RADIUS shared secrets, or key-wrapping material.
- High-availability monitoring is not included. Add it only after importing
  and validating `CISCO-LWAPP-HA-MIB` against the target HA pair.
- Several AP stability and radio values are cumulative counters. Alerting
  should use an appropriate rate or change over time where supported.
- The package contains no SNMP usernames, authentication secrets, privacy
  secrets, device addresses, or environment-specific credentials.

## Troubleshooting

If no data is collected:

1. Run **Inventory > Tools > SNMP System Info** against the controller.
2. Confirm reachability from ThirdEye to UDP port 161 on the controller.
3. Verify the controller's SNMP configuration, access restrictions, and the
   credential assigned in ThirdEye.
4. Confirm that the required Cisco MIB modules and dependencies are loaded in
   ThirdEye.
5. On the controller, use `show snmp mib | include <object-name>` to confirm
   that the IOS XE release implements a specific object used by the set.
6. Wait for the monitor's full collection interval after making a correction.

If scalar metrics work but a table is empty, confirm that the corresponding AP,
radio, WLAN, or RADIUS configuration exists. If a field returns `-`, treat it
as unsupported on that controller/AP combination unless a direct SNMP query
shows otherwise. A broad table can time out on its first collection cycle;
confirm repeated failure on later cycles before changing the definition.
