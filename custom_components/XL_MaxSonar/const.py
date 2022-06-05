from curses import baudrate
import logging

LOGGER = logging.getLogger(__package__)
DOMAIN = "XL_MaxSonar"
SERIAL_PORT = "/dev/ttyAMA0"
BAUDRATE = 9600
NAME = "XL-MaxSonar"
VERSION = "v0.0beta1"
ATTRIBUTION = ""
SENSOR = "distance"
DEFAULT_NAME = "XL_MaxSonar"
