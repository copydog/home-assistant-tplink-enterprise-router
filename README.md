# home-assistant-tplink-enterprise-router

Home Assistant Integration for TP-Link Enterprise Router

> [!WARNING]
> Please temporarily disable the integration before accessing the router admin page. TP-Link admin page only allows one user at a time. This integration will log you out of the admin page every time it scans for updates (every 30s by default).

See [Supported routers](#supports)

<img src="https://raw.githubusercontent.com/copydog/home-assistant-tplink-enterprise-router/refs/heads/main/docs/media/screenshot.png">

## Components
### Events
This feature uses udp system log 

- [ ] [DEBUG MODE ONLY]tplink_enterprise_router_wireless_web_login: Fired when a client (including this integration) logged into web management
- [x] tplink_enterprise_router_wireless_client_roamed: Fired when a client roamed to another access point (AP)
- [x] tplink_enterprise_router_wireless_client_connected: Fired when a client connected
- [x] tplink_enterprise_router_wireless_client_disconnected: Fired when a client disconnected
- [x] tplink_enterprise_router_wireless_client_changed: Fire when a client connected, disconnected or roamed from syslog
- [x] tplink_enterprise_router_wireless_client_updated: Fire when a client connected, disconnected or roamed from syslog and poll
- [ ] tplink_enterprise_router_dhcp_ip_assigned: Fired when router assigned ip to a client
- [ ] tplink_enterprise_router_unstable_wireless_client_detected: Fire when a client connects and disconnects frequently in a short time

### Switches / Buttons
- [x] Reboot
- [x] Refresh
- [x] Polling
- [x] Turn on ap light
- [x] Turn off ap light

### Sensors
- [x] Total amount of clients
- [x] Total amount of wired clients
- [x] Total amount of host wireless clients
- [x] Cpu used
- [x] Memory used
- [x] Wan state
- [x] Network hosts (attribute of data entity)
- [x] Total amount of each ssid (attribute od data entity)

## <a id="supports">Supported routers</a>
- TL-R479GPE-AC (I use this)
- TL-R470GP
- TL-R6812TP-AC (Coming soon)
- other similar series