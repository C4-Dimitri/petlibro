"""Support for PETLIBRO updates."""
from __future__ import annotations
from .api import make_api_call
import aiohttp
from aiohttp import ClientSession, ClientError
from dataclasses import dataclass
from logging import getLogger
from collections.abc import Callable
from datetime import datetime
from typing import Any, cast
from .const import DOMAIN
from homeassistant.components.update.const import UpdateStateClass, UpdateDeviceClass
from homeassistant.components.update import UpdateEntity, UpdateEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry  # Added ConfigEntry import
from .hub import PetLibroHub  # Adjust the import path as necessary

_LOGGER = getLogger(__name__)

from .devices import Device
from .devices.device import Device
from .devices.feeders.feeder import Feeder
from .devices.feeders.air_smart_feeder import AirSmartFeeder
from .devices.feeders.granary_smart_feeder import GranarySmartFeeder
from .devices.feeders.granary_smart_camera_feeder import GranarySmartCameraFeeder
from .devices.feeders.one_rfid_smart_feeder import OneRFIDSmartFeeder
from .devices.feeders.polar_wet_food_feeder import PolarWetFoodFeeder
from .devices.feeders.space_smart_feeder import SpaceSmartFeeder
from .devices.fountains.dockstream_smart_fountain import DockstreamSmartFountain
from .devices.fountains.dockstream_smart_rfid_fountain import DockstreamSmartRFIDFountain
from .entity import PetLibroEntity, _DeviceT, PetLibroEntityDescription

@dataclass(frozen=True)
class PetLibroUpdateEntityDescription(UpdateEntityDescription, PetLibroEntityDescription[_DeviceT]):
    """A class that describes device update entities."""

    icon_fn: Callable[[Any], str | None] = lambda _: None
    native_unit_of_measurement_fn: Callable[[_DeviceT], str | None] = lambda _: None
    device_class_fn: Callable[[_DeviceT], UpdateDeviceClass | None] = lambda _: None
    should_report: Callable[[_DeviceT], bool] = lambda _: True


class PetLibroUpdateEntity(PetLibroEntity[_DeviceT], UpdateEntity):
    """PETLIBRO update entity."""

    entity_description: PetLibroUpdateEntityDescription[_DeviceT]

    def __init__(self, device, hub, description):
        """Initialize the update entity."""
        super().__init__(device, hub, description)
        
        # Ensure unique_id includes the device serial, specific update key, and the MAC address from the device attributes
        mac_address = getattr(device, "mac", None)
        if mac_address:
            self._attr_unique_id = f"{device.serial}-{description.key}-{mac_address.replace(':', '')}"
        else:
            self._attr_unique_id = f"{device.serial}-{description.key}"
        
        # Dictionary to keep track of the last known state for each update key
        self._last_update_state = {}

    @property
    def native_value(self) -> float | datetime | str | None:
        """Return the state."""

        update_key = self.entity_description.key

        # Default behavior for other updates
        if self.entity_description.should_report(self.device):
            val = getattr(self.device, update_key, None)
            # Log only if the state has changed
            if self._last_update_state.get(update_key) != val:
                _LOGGER.debug(f"Raw {update_key} for device {self.device.serial}: {val}")
                self._last_update_state[update_key] = val
            return val
        return None

    @property
    def device_class(self) -> UpdateStateClass | None:
        """Return the device class to use in the frontend, if any."""
        if (device_class := self.entity_description.device_class_fn(self.device)) is not None:
            return device_class
        return super().device_class

DEVICE_SENSOR_MAP: dict[type[Device], list[PetLibroUpdateEntityDescription]] = {
    Feeder: [
    ],
    AirSmartFeeder: [
        PetLibroUpdateEntityDescription[AirSmartFeeder](
            key="device_sn",
            translation_key="device_sn",
            icon="mdi:identifier",
            name="Device SN"
        ),
    ],
    GranarySmartFeeder: [
        PetLibroUpdateEntityDescription[GranarySmartFeeder](
            key="device_sn",
            translation_key="device_sn",
            icon="mdi:identifier",
            name="Device SN",
            device_class=UpdateDeviceClass.FIRMWARE
        ),
    ],
    GranarySmartCameraFeeder: [
        PetLibroUpdateEntityDescription[GranarySmartCameraFeeder](
            key="device_sn",
            translation_key="device_sn",
            icon="mdi:identifier",
            name="Device SN",
            device_class=UpdateDeviceClass.FIRMWARE
        ),
    ],
    OneRFIDSmartFeeder: [
        PetLibroUpdateEntityDescription[OneRFIDSmartFeeder](
            key="device_sn",
            translation_key="device_sn",
            icon="mdi:identifier",
            name="Device SN",
            device_class=UpdateDeviceClass.FIRMWARE
        ),
    ],
    PolarWetFoodFeeder: [
        PetLibroUpdateEntityDescription[PolarWetFoodFeeder](
            key="device_sn",
            translation_key="device_sn",
            icon="mdi:identifier",
            name="Device SN",
            device_class=UpdateDeviceClass.FIRMWARE
        ),
    ],
    SpaceSmartFeeder: [
        PetLibroUpdateEntityDescription[SpaceSmartFeeder](
            key="device_sn",
            translation_key="device_sn",
            icon="mdi:identifier",
            name="Device SN",
            device_class=UpdateDeviceClass.FIRMWARE
        ),
    ],
    DockstreamSmartFountain: [
        PetLibroUpdateEntityDescription[DockstreamSmartFountain](
            key="device_sn",
            translation_key="device_sn",
            icon="mdi:identifier",
            name="Device SN",
            device_class=UpdateDeviceClass.FIRMWARE
        ),
    ],
    DockstreamSmartRFIDFountain: [
        PetLibroUpdateEntityDescription[DockstreamSmartRFIDFountain](
            key="device_sn",
            translation_key="device_sn",
            icon="mdi:identifier",
            name="Device SN",
            device_class=UpdateDeviceClass.FIRMWARE
        ),
    ]
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PETLIBRO updates using config entry."""
    # Retrieve the hub from hass.data that was set up in __init__.py
    hub = hass.data[DOMAIN].get(entry.entry_id)

    if not hub:
        _LOGGER.error("Hub not found for entry: %s", entry.entry_id)
        return

    # Ensure that the devices are loaded
    if not hub.devices:
        _LOGGER.warning("No devices found in hub during update setup.")
        return

    # Log the contents of the hub data for debugging
    _LOGGER.debug("Hub data: %s", hub)

    devices = hub.devices  # Devices should already be loaded in the hub
    _LOGGER.debug("Devices in hub: %s", devices)

    # Create update entities for each device based on the update map
    entities = [
        PetLibroUpdateEntity(device, hub, description)
        for device in devices  # Iterate through devices from the hub
        for device_type, entity_descriptions in DEVICE_SENSOR_MAP.items()
        if isinstance(device, device_type)
        for description in entity_descriptions
    ]

    if not entities:
        _LOGGER.warning("No updates added, entities list is empty!")
    else:
        # Log the number of entities and their details
        _LOGGER.debug("Adding %d PetLibro updates", len(entities))
        for entity in entities:
            _LOGGER.debug("Adding update entity: %s for device %s", entity.entity_description.name, entity.device.name)

        # Add update entities to Home Assistant
        async_add_entities(entities)

