"""The Detailed Hello World Push integration."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

import logging
_LOGGER = logging.getLogger(__name__)

from .xl_maxsonar import XLMaxSonar
from .const import DOMAIN
import serial_asyncio
import asyncio

PLATFORMS: list[str] = ["sensor"]

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the XL-max sonar sensor component."""

    serial_port="/dev/tty"
    baudrate=9600
    timeout=10

    loop = asyncio.get_event_loop()
    coro = serial_asyncio.create_serial_connection(loop, XLMaxSonar, serial_port, baudrate=baudrate)

    #run the server
    transport, protocol = await hass.async_add_job(coro)

    hass.data[DOMAIN] = protocol

    #load sensors
    hass.helpers.discovery.load_platform("sensor", DOMAIN, {}, config)

    return True

