# home-assistant-tplink-enterprise-router

Home Assistant Integration for TP-Link Enterprise Router

> [!WARNING]
> Please temporarily disable the integration before accessing the router admin page. TP-Link admin page only allows one user at a time. This integration will log you out of the admin page every time it scans for updates (every 30s by default).

See [Supported routers](#supports)

<img src="https://raw.githubusercontent.com/copydog/home-assistant-tplink-enterprise-router/refs/heads/main/docs/media/screenshot.png">

## Components
### Events
This feature will be supported, BUT syslog receiver is a BETTER choice

- [ ] tplink_router_device_joined: Fired when a new device appears in your network
- [ ] tplink_router_device_offline: Fired when a device becomes offline
- [ ] tplink_router_device_online: Fired when a device becomes online

### Switches / Buttons
- [x] Reboot
- [x] Running
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
- other similar series