# home-assistant-tplink-enterprise-router

[English](./README_en.md)

Home Assistant Integration for TP-Link Enterprise Router

查看 [支持的路由](#supports)

<img src="https://raw.githubusercontent.com/copydog/home-assistant-tplink-enterprise-router/refs/heads/main/docs/media/screenshot.png">

## 你需要知道的系统设计
- 登陆密码是加密后的密码，自行抓包
- web_login事件是排除了此插件的登陆
- 为保证轮询性能，除非令牌失效，每次调用接口，不再重新登陆
- 为保证本项目最小化，系统日志通知事件会基于homeassistant-syslog-receiver转发事件，有轻微的延迟
- 如遇见极小丢包、乱序风险导致的状态错误，可开启同时开始"系统日志轮询事件"与"系统日志通知事件"
- 客户端实体状态目前只会在轮询的时候更新，如需要实时追踪，使用事件+eventsensor
- 不支持Yaml配置，但支持指定unique_id

## 版本
- 近期发布v1.0.0到hacs

## 组件
### 事件
系统日志事件功能用了 homeassistant-syslog-receiver, 但是要改一些代码，后面我会给作者提交PR

- [x] tplink_enterprise_router_web_login: 每次登陆后台管理页面的时候发送
- [x] tplink_enterprise_router_wireless_client_roamed: 客户端漫游到其他AP设备时发送
- [x] tplink_enterprise_router_wireless_client_connected: 客户端连接到AP时发送
- [x] tplink_enterprise_router_wireless_client_disconnected: 客户端断开连接时发送
- [x] tplink_enterprise_router_wireless_client_changed: 当客户端，断开、连接、漫游、频段切换时发送，仅检测系统日志
- [x] tplink_enterprise_router_dhcp_ip_assigned: 当路由器给客户端分配IP时发送
- [x] tplink_enterprise_router_unstable_wireless_client_detected: 当客户端短时间内频繁连接和断线时发送

### 开关 / 按钮
- [x] 重启路由 / 重启AP / 重启AP和路由
- [x] 刷新
- [x] 轮询状态
- [x] 关闭 / 打开所有AP指示灯
- [x] SSID 启用开关

### 传感器
- [x] 客户端总数 / 有线客户端总数 / 无线客户端总数 / 列表
- [x] CPU 使用率 / 内存使用率
- [x] WAN 总数 / 状态
- [x] SSID 设备统计 / 列表
- [x] AP 总数 / 在线总数 / 离线总数 / 列表
- [x] 客户端实体

## <a id="supports">支持的路由器</a>
- TL-R479GPE-AC (我用这个)
- TL-R470GP-AC
- TL-R6812TP-AC (测试中)
- 其他类似设备