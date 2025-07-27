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
    def latest_version(self) -> str | None:
        """Return the latest firmware version available, or fallback to installed."""
        version = self.device.update_version
        if version:
            return version
        # Fallback: just use installed version so HA doesn't think it's unknown
        return self.installed_version

    @property
    def latest_version(self) -> str:
        version = self.device.update_version or self.installed_version
        _LOGGER.debug("latest_version returning: %s", version)
        return version

    @property
    def release_summary(self) -> str:
        summary = self.device.update_release_notes
        return summary if summary else "Device firmware is up to date."

    @property
    def release_url(self) -> str:
        url = self.device._data.get("getUpgrade", {}).get("upgradeUrl", "")
        return url or ""

    @property
    def title(self) -> str:
        """Return title of the firmware/software."""
        value = f"{self.device.name} Firmware"
        _LOGGER.debug("title returning: %s", value)
        return value

    @property
    def display_precision(self) -> int:
        value = 0
        _LOGGER.debug("display_precision returning: %s", value)
        return value

    @property
    def in_progress(self) -> bool:
        progress = self.device.update_progress
        in_progress = progress is not None and 0.0 < progress < 100.0
        _LOGGER.debug("in_progress returning: %s (progress=%s)", in_progress, progress)
        return in_progress

    @property
    def update_percentage(self) -> float | None:
        progress = self.device.update_progress
        value = float(progress) if progress is not None and 0.0 < progress <= 100.0 else None
        _LOGGER.debug("update_percentage returning: %s (raw progress=%s)", value, progress)
        return value

    @property
    def available(self) -> bool:
        return True

    async def async_install(self, version: str | None, backup: bool, **kwargs):
        _LOGGER.debug("Install called with version=%s backup=%s kwargs=%s", version, backup, kwargs)

        upgrade_data = self.device._data.get("getUpgrade", {})
        job_item_id = upgrade_data.get("jobItemId")

        if not job_item_id:
            _LOGGER.warning("No firmware update available for %s", self.device.name)
            return

        _LOGGER.debug("Triggering firmware update for %s (jobItemId=%s)", self.device.name, job_item_id)
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

