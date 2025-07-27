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
from homeassistant.components.update import UpdateDeviceClass, UpdateEntity, UpdateEntityDescription, UpdateEntityFeature
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
    """Describes PetLibro update entity."""


class PetLibroUpdateEntity(PetLibroEntity[_DeviceT], UpdateEntity):
    """PETLIBRO update entity."""

    entity_description: PetLibroUpdateEntityDescription[_DeviceT]

    def __init__(self, device, hub, description):
        """Initialize the update entity."""
        super().__init__(device, hub, description)

        mac_address = getattr(device, "mac", None)
        if mac_address:
            self._attr_unique_id = f"{device.serial}-{description.key}-{mac_address.replace(':', '')}"
        else:
            self._attr_unique_id = f"{device.serial}-{description.key}"

        self._attr_device_class = UpdateDeviceClass.FIRMWARE
        self._attr_supported_features = (
            UpdateEntityFeature.INSTALL
            | UpdateEntityFeature.PROGRESS
            | UpdateEntityFeature.RELEASE_NOTES
        )
        self._attr_title = f"{device.name} Firmware"

    @property
    def installed_version(self) -> str | None:
        """Return the currently installed firmware version."""
        return getattr(self.device, "software_version", None)

    @property
    def latest_version(self) -> str | None:
        """Return the latest firmware version available."""
        return self.device.update_version

    @property
    def release_summary(self) -> str | None:
        """Return release notes (if any)."""
        upgrade_data = self.device._data.get("getUpgrade")
        _LOGGER.debug("release_url raw data: %s", upgrade_data)
        return self.device.update_release_notes

    @property
    def release_url(self) -> str | None:
        """Return firmware download URL."""
        upgrade_data = self.device._data.get("getUpgrade")
        _LOGGER.debug("release_url raw data: %s", upgrade_data)
        return upgrade_data.get("upgradeUrl") if upgrade_data else None

    @property
    def in_progress(self) -> bool:
        """Return if an update is currently in progress."""
        upgrade_data = self.device._data.get("getUpgrade")
        _LOGGER.debug("release_url raw data: %s", upgrade_data)
        return 0.0 < self.device.update_progress < 100.0    

    @property
    def update_percentage(self) -> float | None:
        """Return update installation progress as 0-100% or None."""
        upgrade_data = self.device._data.get("getUpgrade")
        _LOGGER.debug("release_url raw data: %s", upgrade_data)
        progress = self.device.update_progress
        _LOGGER.debug("release_url raw data: %s", progress)
        # Always return 0 if progress is 0 instead of None
        return round(progress, 1)

    @property
    def available(self) -> bool:
        """Return True if updates are available."""
        upgrade_data = self.device._data.get("getUpgrade")
        _LOGGER.debug("release_url raw data: %s", upgrade_data)
        return self.device.update_available

    async def async_install(self, version: str | None, backup: bool, **kwargs):
        """Trigger firmware update on the device."""
        _ = version
        _ = kwargs  # We don’t use version or kwargs for now.

        upgrade_data = self.device._data.get("getUpgrade", {})
        job_item_id = upgrade_data.get("jobItemId")

        if not job_item_id:
            _LOGGER.warning("No firmware update available for %s", self.device.name)
            return

        _LOGGER.debug("Triggering firmware update for %s", self.device.name)
        await self.device.api.trigger_firmware_upgrade(self.device.serial, job_item_id)

DEVICE_UPDATE_MAP: dict[type[Device], list[PetLibroUpdateEntityDescription]] = {
    Feeder: [
    ],
    AirSmartFeeder: [
        PetLibroUpdateEntityDescription[AirSmartFeeder](
            key="firmware",
        ),
    ],
    GranarySmartFeeder: [
        PetLibroUpdateEntityDescription[GranarySmartFeeder](
            key="firmware",
        ),
    ],
    GranarySmartCameraFeeder: [
        PetLibroUpdateEntityDescription[GranarySmartCameraFeeder](
            key="firmware",
        ),
    ],
    OneRFIDSmartFeeder: [
        PetLibroUpdateEntityDescription[OneRFIDSmartFeeder](
            key="firmware",
        ),
    ],
    PolarWetFoodFeeder: [
        PetLibroUpdateEntityDescription[PolarWetFoodFeeder](
            key="firmware",
        ),
    ],
    SpaceSmartFeeder: [
        PetLibroUpdateEntityDescription[SpaceSmartFeeder](
            key="firmware",
        ),
    ],
    DockstreamSmartFountain: [
        PetLibroUpdateEntityDescription[DockstreamSmartFountain](
            key="firmware",
        ),
    ],
    DockstreamSmartRFIDFountain: [
        PetLibroUpdateEntityDescription[DockstreamSmartRFIDFountain](
            key="firmware",
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
        for device_type, entity_descriptions in DEVICE_UPDATE_MAP.items()
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

