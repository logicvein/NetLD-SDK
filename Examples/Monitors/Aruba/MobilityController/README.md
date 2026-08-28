# ArubaOS Mobility Controller Operational Collection

Last updated: 2026-08-28

Tested against: Aruba 7010 running ArubaOS 8.12.0.1 SSR (build 89864)

This example monitor set provides operational visibility into an ArubaOS
Mobility Controller's wireless-control role. It collects controller role and
configuration state, software and reload information, AP and user demand,
per-AP state and restart history, radio state and capacity, ESSID availability,
authentication-server health, controller licenses, and HA profile and heartbeat
state.

The collection is intended as a starting point. It does not include alert
policies or environment-specific thresholds. Generic CPU, memory, storage,
interface, and uptime monitoring are outside its scope.

## Requirements

Before importing the monitor set, confirm that:

- The ArubaOS controller has been added to the ThirdEye inventory.
- ThirdEye can reach the controller's SNMP agent, normally over UDP port 161.
- SNMP is enabled on the controller and permits queries from the ThirdEye
  server. SNMPv3 with authentication and privacy is recommended.
- A matching SNMP credential has been assigned to the device in ThirdEye.
- The ArubaOS controller MIB modules and their dependencies have been imported
  into ThirdEye.

The collection uses these Aruba modules:

- `WLSX-SYSTEMEXT-MIB`
- `WLSX-WLAN-MIB`
- `WLSX-USER-MIB`
- `WLSX-AUTH-MIB`
- `WLSX-HA-MIB`
- `ARUBA-TC`
- `ARUBA-MIB`

The example was developed from the ArubaOS MIB files bundled with the tested
ThirdEye installation. The source files identify themselves as part of an
ArubaOS 8.13.2.0 MIB package, while the individual WLSX modules retain module
revision metadata dated 2020. Other ArubaOS and MIB versions should be
validated before production use.

The ArubaOS MIB files are not included with this example.

### Obtaining the ArubaOS MIBs

Download the MIB package that corresponds to the ArubaOS release being
monitored from the Aruba Support site:

1. Sign in to the Aruba Support site.
2. Open **Download Software > ArubaOS**.
3. Open the folder for the required ArubaOS release.
4. Download the corresponding MIB archive and extract it locally.

Import the required WLSX modules together with `ARUBA-TC`, `ARUBA-MIB`, and
their standard SNMP dependencies so ThirdEye can resolve the Aruba textual
conventions used by the monitor set.

For additional information, see HPE Aruba Networking's documentation for
[ArubaOS MIB files](https://arubanetworking.hpe.com/techdocs/ArubaOS/AOS_8x_WebHelp/Content/arubaos-solutions/manage-utilities/mib-file.htm).

## Installation

1. Import the required ArubaOS MIB modules if they are not already available.
2. In **Inventory**, use **Tools > SNMP System Info** to verify that ThirdEye
   can query each target controller.
3. Go to **Monitors > Sets** and import
   `ArubaOS Mobility Controller - Operational Collection.3em`.
4. Assign **ArubaOS Mobility Controller - Operational Collection** to the
   appropriate ArubaOS controllers.
5. Wait at least fifteen minutes so every monitor has had a collection
   opportunity, then review the results for each assigned device.

Automatic assignment to newly discovered devices is disabled. Review the set
before enabling automatic assignment in any environment.

## Included monitors

The set contains ten SNMP monitors. Stateful operational topics collect every
minute. Software, reload, and license information collect every fifteen
minutes.

### Controller Role and Configuration State — 1 minute

- `wlsxSysExtSwitchRole`
- `wlsxSysExtSwitchConductorIp`
- `wlsxSysExtMMSConfigID`
- `wlsxSysExtControllerConfigID`
- `wlsxSysExtIsMMSConfigUpdateEnabled`

This group establishes the controller's Aruba domain role, its Conductor
relationship, and the configuration identifiers used to detect management or
configuration-state changes.

### Software and Reload State — 15 minutes

- `wlsxSysExtHwVersion`
- `wlsxSysExtSwVersion`
- `wlsxSysExtSwitchLastReload`

### Wireless Demand — 1 minute

- `wlsxWlanTotalNumAccessPoints`
- `wlsxWlanTotalNumStationsAssociated`
- `wlsxTotalNumOfUsers`
- `wlsxNumOfUsers8021x`
- `wlsxNumOfUsersVPN`
- `wlsxNumOfUsersCP`
- `wlsxNumOfUsersMAC`
- `wlsxNumOfUsersStateful8021x`

Associated stations and controller users are intentionally collected
separately. They can diverge because the user table can include wired, VPN, or
other authenticated sessions that are not currently associated wireless
stations.

### Access Point State and Stability — 1 minute

From `WLSX-WLAN-MIB::wlsxWlanAPTable`:

- `wlanAPName`
- `wlanAPIpAddress`
- `wlanAPGroupName`
- `wlanAPModelName`
- `wlanAPStatus`
- `wlanAPUpTime`
- `wlanAPNumBootstraps`
- `wlanAPNumReboots`
- `wlanAPNumWarmReboots`
- `wlanAPSwVersion`

This table distinguishes known AP inventory from currently connected APs and
retains restart evidence that can expose AP instability.

### Radio State and Capacity — 1 minute

From `WLSX-WLAN-MIB::wlsxWlanRadioTable`:

- `wlanAPRadioAPName`
- `wlanAPRadioType`
- `wlanAPRadioChannel`
- `wlanAPRadioTransmitPower10x`
- `wlanAPRadioMode`
- `wlanAPRadioUtilization`
- `wlanAPRadioNumAssociatedClients`
- `wlanAPRadioNumActiveBSSIDs`
- `wlanAPRadioHTMode`

The transmit-power value is reported in tenths of a unit by the Aruba MIB.
Radio rows can be absent when no APs are currently connected.

### ESSID Service State — 1 minute

From `WLSX-WLAN-MIB::wlsxWlanESSIDTable`:

- `wlanESSIDNumStations`
- `wlanESSIDNumAccessPointsUp`
- `wlanESSIDNumAccessPointsDown`
- `wlanESSIDEncryptionType`

The ESSID is the table index. An empty table is expected when the controller
has no active ESSID/AP state to report.

### Authentication Server Health — 1 minute

From `WLSX-AUTH-MIB::wlsxAuthenticationServerTable`:

- `authServerAddress`
- `authServerType`
- `authServerState`
- `authServerInservice`
- `authServerUsageCount`
- `authServerSuccessfullAuths`
- `authServerFailedAuths`
- `authServerTimeouts`
- `authServerAvgResponseTime`
- `authServerOutStandingRequests`

Usage, success, failure, and timeout values are cumulative counters. Alerting
should use changes over time where supported.

### Controller License Status — 15 minutes

From `WLSX-SYSTEMEXT-MIB::wlsxSysExtSwitchLicenseTable`:

- `sysExtLicenseService`
- `sysExtLicenseInstalled`
- `sysExtLicenseExpires`
- `sysExtLicenseFlags`

The license key is deliberately excluded.

### HA Profile and AP State — 1 minute

From the HA configuration and AP-count tables:

- `haMembership`
- `haState`
- `haRole`
- `haStateSync`
- `haIntercontrollerHbt`
- `haActiveAPs`
- `haStandbyAPs`
- `haTotalAPs`

The HA pre-shared key is deliberately excluded.

### HA Heartbeat Health — 1 minute

From `WLSX-HA-MIB::wlsxIntercontrollerHbtTable`:

- `haActiveCtrlIp`
- `haReferenceCnt`
- `haTotalHbtRequestsSent`
- `haTotalHbtResponsesRcvd`
- `haLastMissedHbtCnt`
- `haLastHbtMissedTime`

This table is empty on a controller without an active inter-controller HA
heartbeat relationship.

## Expected variations

- AP, radio, and ESSID tables depend on the controller having relevant AP and
  WLAN state. A controller can retain known AP records while reporting zero
  currently connected APs.
- Authentication-server rows depend on configured internal or external
  authentication services.
- HA profile and heartbeat tables depend on the controller's redundancy
  configuration. Empty heartbeat data is expected when HA is disabled.
- License date and flag formats can vary by ArubaOS release and license type.
- Conductor terminology replaces the older `master` terminology in current
  ArubaOS MIB objects.

## Validation

To run the **SNMP System Info** tool, open **Inventory**, select the target
controller, open **Tools**, and select **SNMP System Info**. ThirdEye queries
the device using its assigned SNMP credential. A successful test returns basic
system information, including the system description and uptime, rather than
an SNMP timeout or authentication error.

After installation:

1. Run **SNMP System Info** for every assigned controller and confirm that it
   succeeds.
2. Confirm current data for the controller-role and wireless-demand monitors.
3. Compare AP state, radio state, ESSID state, AAA servers, and HA state with
   the ArubaOS interface before creating thresholds.
4. Wait through the fifteen-minute interval and verify software and license
   collection.
5. Treat an empty feature-specific table as an environment check, not an
   automatic fault.

## Limitations

- The example performs collection only; it installs no alert policies,
  notification destinations, or incident workflows.
- The set does not collect client MAC addresses, usernames, per-client traffic,
  or other high-cardinality station/user tables.
- It does not collect license keys or HA pre-shared keys.
- AOS 10 gateways and Aruba Central-managed cloud objects use different APIs
  and should not be assumed to match this ArubaOS controller collection.
- The package contains no SNMP usernames, authentication secrets, privacy
  secrets, device addresses, or environment-specific credentials.

## Troubleshooting

If no data is collected:

1. Run **Inventory > Tools > SNMP System Info** against the controller.
2. Confirm reachability from ThirdEye to UDP port 161.
3. Verify the controller's SNMP configuration and assigned ThirdEye credential.
4. Confirm that the required WLSX and Aruba textual-convention MIBs are loaded.
5. Wait for the monitor's full collection interval.

If scalar metrics work but a table is empty, confirm that the corresponding AP,
ESSID, AAA, license, or HA feature is active before treating it as a collection
failure. A transient first-pass timeout can occur when several new table probes
begin simultaneously; confirm the result on the next scheduled cycle before
changing the definition.
