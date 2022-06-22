"""The Detailed Hello World Push integration."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

import logging
_LOGGER = logging.getLogger(__name__)

from .xl_maxsonar import XLMaxSonar
from .const import DOMAIN

PLATFORMS: list[str] = ["sensor"]

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the XL-max sonar sensor component."""

    server = XLMaxSonar(serial_port="/dev/ttyAMA0", baudrate=9600, timeout=10)
    hass.data[DOMAIN] = server

    #load sensors
    hass.helpers.discovery.load_platform("sensor", DOMAIN, {}, config)

    #run the server 
    hass.async_add_job(server.run())

    return True


