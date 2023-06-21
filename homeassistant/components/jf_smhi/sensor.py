"""Platform for sensor integration."""

from __future__ import annotations

from datetime import timedelta

import requests

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import Throttle

from .const import SMHI_BASE_URL

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=31)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_devices: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_devices(
        [JfSMHISensor(hass=hass, hours_ahead=config_entry.data["hoursAhead"])]
    )


class JfSMHISensor(SensorEntity):
    """Representation of a Sensor."""

    _attr_name = "Min Temp In Timespan"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, hass: HomeAssistant, hours_ahead: int) -> None:
        """Init the sensor."""
        self.hours_ahead = hours_ahead
        self.hass = hass

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self) -> None:
        """Fetch the latest weather forecast data from SMHI."""
        version = 2
        longitude = self.hass.config.longitude
        latitude = self.hass.config.latitude
        # hours_ahead = 12

        forcaste_url = (
            SMHI_BASE_URL
            + f'/api/category/{"pmp3g"}/version/{version}/geotype/point/lon/{longitude:.6f}/lat/{latitude:.6f}/data.json'
        )
        res = requests.get(forcaste_url, timeout=30)
        if res.ok:
            data = res.json()

            min_temp = 999999
            for i in range(0, self.hours_ahead):
                for para in data["timeSeries"][i]["parameters"]:
                    if para["name"] == "t":
                        if para["values"][0] < min_temp:
                            min_temp = para["values"][0]

            self._attr_native_value = min_temp
