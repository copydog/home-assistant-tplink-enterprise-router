# home-assistant-tplink-enterprise-router

[English](./README_en.md)

Home Assistant Integration for TP-Link Enterprise Router

> [!WARNING]
> 你可以通过关闭 轮询状态开关 来停止轮询，这样就不会每次轮询的时候把你踢下线

查看 [支持的路由](#supports)

<img src="https://raw.githubusercontent.com/copydog/home-assistant-tplink-enterprise-router/refs/heads/main/docs/media/screenshot.png">

## 开发路线
- [ ] 所有事件相关
- [ ] 一键重启AP
- [ ] 一键自动射频调优
- [ ] SSID 启用开关、隐藏开关
- [ ] 系统日志丢包检测与修复
- [ ] TP-LINK交换机: TL-SG2024MP 8.0 (新开项目)

## 组件
### 事件
这个功能用了 homeassistant-syslog-receiver, 但是要改一些代码，后面我会给作者提交PR

- [ ] [仅测试模式]tplink_enterprise_router_wireless_web_login: 每次登陆后台管理页面的时候发送
- [x] tplink_enterprise_router_wireless_client_roamed: 客户端漫游到其他AP设备时发送
- [x] tplink_enterprise_router_wireless_client_connected: 客户端连接到AP时发送
- [x] tplink_enterprise_router_wireless_client_disconnected: 客户端断开连接时发送
- [x] tplink_enterprise_router_wireless_client_changed: 当客户端，断开、连接、漫游、频段切换时发送，仅检测系统日志
- [x] tplink_enterprise_router_wireless_client_updated: 当客户端，断开、连接、漫游、频段切换时发送，与changed不同的是轮询的数据也会发送
- [ ] tplink_enterprise_router_dhcp_ip_assigned: 当路由器给客户端分配IP时发送
- [ ] tplink_enterprise_router_unstable_wireless_client_detected: 当客户端短时间内频繁连接和断线时发送

### Switches / Buttons
- [x] 重启
- [x] 刷新
- [x] 轮询状态
- [x] 打开所有AP指示灯
- [x] 关闭所有AP指示灯

### Sensors
- [x] 客户端总数
- [x] 有线客户端总数
- [x] 无线客户端总数
- [x] CPU 使用率
- [x] 内存使用率
- [x] WAN 总数
- [x] WAN 状态
- [x] SSID 设备统计
- [x] AP 连接设备统计 

## <a id="supports">支持的路由器</a>
- TL-R479GPE-AC (I use this)
- TL-R470GP
- TL-R6812TP-AC (testing)
- 其他类似设备