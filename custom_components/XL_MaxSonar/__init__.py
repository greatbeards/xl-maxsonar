"""The Detailed Hello World Push integration."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

import logging
_LOGGER = logging.getLogger(__name__)

from .solis_solarman import SolarmanServer, solis_inverter_fields
from .const import DOMAIN

PLATFORMS: list[str] = ["sensor"]

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the solis solarman component."""

    #TODO: Use the config to specify invertor fields [to enable support for other formats.]
    server = SolarmanServer(solis_inverter_fields)
    hass.data[DOMAIN] = server

    #load sensors
    hass.helpers.discovery.load_platform("sensor", DOMAIN, {}, config)

    #run the server 
    hass.async_add_job(server.run())

    return True


