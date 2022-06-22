"""Platform for sensor integration."""

from homeassistant.components.sensor import (
    STATE_CLASS_MEASUREMENT,
    STATE_CLASS_TOTAL_INCREASING,
    STATE_CLASS_TOTAL,
    SensorEntity,
    SensorEntityDescription,
)

from homeassistant.const import (
    DEVICE_CLASS_ENERGY,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_CURRENT,
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_VOLTAGE,
    FREQUENCY_HERTZ,
    PERCENTAGE,
    DEVICE_CLASS_VOLTAGE,
    ENERGY_KILO_WATT_HOUR,
    POWER_KILO_WATT,
    PERCENTAGE,
    POWER_WATT,
    FREQUENCY_HERTZ,
    ELECTRIC_CURRENT_AMPERE,
    TEMP_CELSIUS,
    ELECTRIC_POTENTIAL_VOLT,
    LENGTH_METERS
)

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

import logging
_LOGGER = logging.getLogger(__name__)

from .xl_maxsonar import XLMaxSonar
from .const import DOMAIN


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType,
) -> None:
    """Set up the sensor platform."""

    server = hass.data[DOMAIN]

    #TODO: use device ID from config
    device_id = "one"
    new_devices = []


    descr = SensorEntityDescription(
        key = 'distance',
        name = 'distance',
        native_unit_of_measurement = LENGTH_METERS,
        #device_class=,
        #state_class=_extract_state_class(name),
    )

    new_devices.append(Sensor(device_id, descr, server))

    #Sensor(device_id, descr, server)
    #for name in server.get_fields():
    #    descr = create_entity_descr(name)
    #    new_devices.append(Sensor(device_id, descr, server))
    if new_devices:
        add_entities(new_devices)
        _LOGGER.warning(f"Added new devices {new_devices}")


def _extract_state_class(name: str):
    if "total" in name.lower() or "daily" in name.lower():
        return STATE_CLASS_TOTAL_INCREASING
    return STATE_CLASS_MEASUREMENT


def _extract_device_class(name):
    t = name.split("_")[-1]

    dev_class_dict = {
        "W": DEVICE_CLASS_POWER,
        "kWh": DEVICE_CLASS_ENERGY,
        "V": DEVICE_CLASS_VOLTAGE,
        "A": DEVICE_CLASS_CURRENT,
        "C": DEVICE_CLASS_TEMPERATURE,
    }

    if t in dev_class_dict:
        return dev_class_dict[t]
    else:
        return None


def _extract_unit(name: str):
    t = name.split("_")[-1]

    unit_dict = {
        "W": POWER_WATT,
        "kWh": ENERGY_KILO_WATT_HOUR,
        "V": ELECTRIC_POTENTIAL_VOLT,
        "A": ELECTRIC_CURRENT_AMPERE,
        "Hz": FREQUENCY_HERTZ,
        "%": PERCENTAGE,
        "C": TEMP_CELSIUS,
    }

    if t in unit_dict:
        return unit_dict[t]
    else:
        return PERCENTAGE

def create_entity_descr(name):
    '''The unit, state and device class are extracted for the name'''
    sed = SensorEntityDescription(
        key=name,
        name=name.replace("_", " "),
        native_unit_of_measurement=_extract_unit(name),
        device_class=_extract_device_class(name),
        state_class=_extract_state_class(name),
    )
    return sed

class Sensor(SensorEntity):
    """Base representation of a Sensor."""

    should_poll = False

    def __init__(
        self, device_id, descr: SensorEntityDescription, server: XLMaxSonar
    ):
        """Initialize the sensor."""
        self.entity_description = descr
        self._name = descr.key
        self._state = 0
        self._device_id = device_id
        self._server = server

    @property
    def device_info(self):
        """Return information to link this entity with the correct device."""
        return {"identifiers": {(DOMAIN, self._device_id)}}

    @property
    def unique_id(self):
        """Return Unique ID string."""
        return f"{self._device_id}_{self._name}"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._server.get_value(self._name)

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._name}"

    #@property
    #def available(self) -> bool:
    #    """Return True if roller and hub is available."""
    #    return True

    async def async_added_to_hass(self):
        """Run when this Entity has been added to HA."""
        self._server.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        """Entity being removed from hass."""
        self._server.remove_callback(self.async_write_ha_state)
