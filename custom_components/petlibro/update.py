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

        # **Default values to avoid None**
        self._attr_installed_version = "0.0.0"
        self._attr_latest_version = "0.0.0"
        self._attr_release_summary = "Device firmware status unknown"
        self._attr_release_url = ""
        self._attr_display_precision = 0
        self._attr_in_progress = False
        self._attr_update_percentage = None
        self._attr_available = True

    @property
    def installed_version(self) -> str:
        version = getattr(self.device, "software_version", None)
        value = version if version else self._attr_installed_version
        _LOGGER.debug("installed_version returning: %s", value)
        return value

    @property
    def latest_version(self) -> str:
        version = self.device.update_version or self.installed_version
        value = version if version else self._attr_latest_version
        _LOGGER.debug("latest_version returning: %s", value)
        return value

    @property
    def release_summary(self) -> str:
        summary = self.device.update_release_notes
        value = summary if summary else self._attr_release_summary
        _LOGGER.debug("release_summary returning: %s", value)
        return value

    @property
    def release_url(self) -> str:
        url = self.device._data.get("getUpgrade", {}).get("upgradeUrl", "")
        value = url if url else self._attr_release_url
        _LOGGER.debug("release_url returning: %s", value)
        return value

    @property
    def title(self) -> str:
        value = f"{self.device.name} Firmware" if self.device.name else self._attr_title
        _LOGGER.debug("title returning: %s", value)
        return value

    @property
    def display_precision(self) -> int:
        value = self._attr_display_precision
        _LOGGER.debug("display_precision returning: %s", value)
        return value

    @property
    def in_progress(self) -> bool:
        progress = self.device.update_progress
        in_progress = progress is not None and 0.0 < progress < 100.0
        value = in_progress if in_progress is not None else self._attr_in_progress
        _LOGGER.debug("in_progress returning: %s (progress=%s)", value, progress)
        return value

    @property
    def update_percentage(self) -> float | None:
        progress = self.device.update_progress
        value = float(progress) if progress is not None and 0.0 < progress <= 100.0 else self._attr_update_percentage
        _LOGGER.debug("update_percentage returning: %s (raw progress=%s)", value, progress)
        return value

    @property
    def available(self) -> bool:
        value = True
        _LOGGER.debug("available returning: %s", value)
        return value

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

