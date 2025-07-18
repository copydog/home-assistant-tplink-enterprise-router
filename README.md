# home-assistant-tplink-enterprise-router

[English](./README_en.md)

Home Assistant Integration for TP-Link Enterprise Router

> [!WARNING]
> 你可以通过关闭 轮询状态开关 来停止轮询，这样就不会每次轮询的时候把你踢下线

查看 [支持的路由](#supports)

<img src="https://raw.githubusercontent.com/copydog/home-assistant-tplink-enterprise-router/refs/heads/main/docs/media/screenshot.png">

## 开发路线
- [ ] 所有未完成组
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

### 开关 / 按钮
- [x] 重启
- [x] 刷新
- [x] 轮询状态
- [x] 打开所有AP指示灯
- [x] 关闭所有AP指示灯
- [ ] 重启所有AP
- [ ] 一键射频调优
- [ ] SSID 启用开关、隐藏开关

### 传感器
- [x] 客户端总数 / 有线客户端总数 / 无线客户端总数 / 列表
- [x] CPU 使用率 / 内存使用率
- [x] WAN 总数 / 状态
- [x] SSID 设备统计 / 列表
- [x] AP 总数 / 在线总数 / 离线总数 / 列表

## <a id="supports">支持的路由器</a>
- TL-R479GPE-AC (我用这个)
- TL-R470GP-AC
- TL-R6812TP-AC (测试中)
- 其他类似设备