"""Constants for the NAD Receiver integration."""
from typing import Final

DOMAIN: Final = "nad"

CONF_TYPE_SERIAL: Final = "RS232"
CONF_TYPE_TELNET: Final = "Telnet"
CONF_TYPE_TCP: Final = "TCP"

CONF_SERIAL_PORT: Final = "serial_port"  # for NADReceiver
CONF_MANUAL_PATH: Final = "manual_path"
CONF_DEFAULT_PORT: Final = 53

CONF_MIN_VOLUME: Final = "min_volume"
CONF_MAX_VOLUME: Final = "max_volume"
CONF_VOLUME_STEP: Final = "volume_step"  # for NADReceiverTCP
CONF_SOURCE_DICT: Final = "sources"  # for NADReceiver

CONF_DEFAULT_MIN_VOLUME: Final = -92
CONF_DEFAULT_MAX_VOLUME: Final = -20
CONF_DEFAULT_VOLUME_STEP: Final = 4
