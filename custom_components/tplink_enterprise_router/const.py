"""Constants"""
DOMAIN = "tplink_enterprise_router"
DEFAULT_NAME = "TP Link Enterprise Router"
DEFAULT_HOST = "http://192.168.0.1"
DEFAULT_INSTANCE_NAME = "TP Link Enterprise Router"
PLATFORMS = ["sensor", "button", "switch", "device_tracker"]
MIN_SEVERITY_LEVELS = {
    "emerg": 0,
    "alert": 1,
    "crit": 2,
    "err": 3,
    "warning": 4,
    "notice": 5,
    "info": 6,
    "debug": 7
}