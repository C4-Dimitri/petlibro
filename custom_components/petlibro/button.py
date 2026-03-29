"""Support for PETLIBRO buttons."""
from __future__ import annotations
import re
from .api import make_api_call
import aiohttp
from aiohttp import ClientSession, ClientError
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any, Generic
from logging import getLogger
from .const import DOMAIN
from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry  # Added ConfigEntry import
from .hub import PetLibroHub  # Adjust the import path as necessary

_LOGGER = getLogger(__name__)

from .entity import PetLibroEntity, _DeviceT, PetLibroEntityDescription
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
from .devices.fountains.dockstream_2_smart_cordless_fountain import Dockstream2SmartCordlessFountain
from .devices.fountains.dockstream_2_smart_fountain import Dockstream2SmartFountain
from .devices.litterboxes.luma_smart_litter_box import LumaSmartLitterBox

@dataclass(frozen=True)
class RequiredKeysMixin(Generic[_DeviceT]):
    """A class that describes devices button entity required keys."""
    set_fn: Callable[[_DeviceT], Coroutine[Any, Any, None]]


@dataclass(frozen=True)
class PetLibroButtonEntityDescription(ButtonEntityDescription, PetLibroEntityDescription[_DeviceT], RequiredKeysMixin[_DeviceT]):
    """A class that describes device button entities."""
    entity_category: EntityCategory = EntityCategory.CONFIG


# Map buttons to their respective device types
DEVICE_BUTTON_MAP: dict[type[Device], list[PetLibroButtonEntityDescription]] = {
    Feeder: [
    ],
    AirSmartFeeder: [
        PetLibroButtonEntityDescription[AirSmartFeeder](
            key="manual_feed",
            translation_key="manual_feed",
            set_fn=lambda device: device.set_manual_feed(),
            name="Manual Feed"
        ),
        PetLibroButtonEntityDescription[AirSmartFeeder](
            key="enable_feeding_plan",
            translation_key="enable_feeding_plan",
            set_fn=lambda device: device.set_feeding_plan(True),
            name="Enable Feeding Plan"
        ),
        PetLibroButtonEntityDescription[AirSmartFeeder](
            key="disable_feeding_plan",
            translation_key="disable_feeding_plan",
            set_fn=lambda device: device.set_feeding_plan(False),
            name="Disable Feeding Plan"
        ),
        PetLibroButtonEntityDescription[AirSmartFeeder](
            key="light_on",
            translation_key="light_on",
            set_fn=lambda device: device.set_light_on(),
            name="Turn On Indicator"
        ),
        PetLibroButtonEntityDescription[AirSmartFeeder](
            key="light_off",
            translation_key="light_off",
            set_fn=lambda device: device.set_light_off(),
            name="Turn Off Indicator"
        ),
    ],
    GranarySmartFeeder: [
        PetLibroButtonEntityDescription[GranarySmartFeeder](
            key="manual_feed",
            translation_key="manual_feed",
            set_fn=lambda device: device.set_manual_feed(),
            name="Manual Feed"
        ),
        PetLibroButtonEntityDescription[GranarySmartFeeder](
            key="enable_feeding_plan",
            translation_key="enable_feeding_plan",
            set_fn=lambda device: device.set_feeding_plan(True),
            name="Enable Feeding Plan"
        ),
        PetLibroButtonEntityDescription[GranarySmartFeeder](
            key="disable_feeding_plan",
            translation_key="disable_feeding_plan",
            set_fn=lambda device: device.set_feeding_plan(False),
            name="Disable Feeding Plan"
        ),
        PetLibroButtonEntityDescription[GranarySmartFeeder](
            key="light_on",
            translation_key="light_on",
            set_fn=lambda device: device.set_light_on(),
            name="Turn On Indicator"
        ),
        PetLibroButtonEntityDescription[GranarySmartFeeder](
            key="light_off",
            translation_key="light_off",
            set_fn=lambda device: device.set_light_off(),
            name="Turn Off Indicator"
        ),
        PetLibroButtonEntityDescription[GranarySmartFeeder](
            key="desiccant_reset",
            translation_key="desiccant_reset",
            set_fn=lambda device: device.set_desiccant_reset(),
            name="Desiccant Replaced"
        ),
    ],
    GranarySmartCameraFeeder: [
        PetLibroButtonEntityDescription[GranarySmartCameraFeeder](
            key="manual_feed",
            translation_key="manual_feed",
            set_fn=lambda device: device.set_manual_feed(),
            name="Manual Feed"
        ),
        PetLibroButtonEntityDescription[GranarySmartCameraFeeder](
            key="enable_feeding_plan",
            translation_key="enable_feeding_plan",
            set_fn=lambda device: device.set_feeding_plan(True),
            name="Enable Feeding Plan"
        ),
        PetLibroButtonEntityDescription[GranarySmartCameraFeeder](
            key="disable_feeding_plan",
            translation_key="disable_feeding_plan",
            set_fn=lambda device: device.set_feeding_plan(False),
            name="Disable Feeding Plan"
        ),
        PetLibroButtonEntityDescription[GranarySmartCameraFeeder](
            key="light_on",
            translation_key="light_on",
            set_fn=lambda device: device.set_light_on(),
            name="Turn On Indicator"
        ),
        PetLibroButtonEntityDescription[GranarySmartCameraFeeder](
            key="light_off",
            translation_key="light_off",
            set_fn=lambda device: device.set_light_off(),
            name="Turn Off Indicator"
        ),
        PetLibroButtonEntityDescription[GranarySmartCameraFeeder](
            key="desiccant_reset",
            translation_key="desiccant_reset",
            set_fn=lambda device: device.set_desiccant_reset(),
            name="Desiccant Replaced"
        ),
    ],
    OneRFIDSmartFeeder: [
        PetLibroButtonEntityDescription[OneRFIDSmartFeeder](
            key="manual_feed",
            translation_key="manual_feed",
            set_fn=lambda device: device.set_manual_feed(),
            name="Manual Feed"
        ),
        PetLibroButtonEntityDescription[OneRFIDSmartFeeder](
            key="enable_feeding_plan",
            translation_key="enable_feeding_plan",
            set_fn=lambda device: device.set_feeding_plan(True),
            name="Enable Feeding Plan"
        ),
        PetLibroButtonEntityDescription[OneRFIDSmartFeeder](
            key="disable_feeding_plan",
            translation_key="disable_feeding_plan",
            set_fn=lambda device: device.set_feeding_plan(False),
            name="Disable Feeding Plan"
        ),
        PetLibroButtonEntityDescription[OneRFIDSmartFeeder](
            key="manual_lid_open",
            translation_key="manual_lid_open",
            set_fn=lambda device: device.set_manual_lid_open(),
            name="Manually Open Lid"
        ),
        PetLibroButtonEntityDescription[OneRFIDSmartFeeder](
            key="display_on",
            translation_key="display_on",
            set_fn=lambda device: device.set_display_on(),
            name="Turn On Display"
        ),
        PetLibroButtonEntityDescription[OneRFIDSmartFeeder](
            key="display_off",
            translation_key="display_off",
            set_fn=lambda device: device.set_display_off(),
            name="Turn Off Display"
        ),
        PetLibroButtonEntityDescription[OneRFIDSmartFeeder](
            key="sound_on",
            translation_key="sound_on",
            set_fn=lambda device: device.set_sound_on(),
            name="Turn On Sound"
        ),
        PetLibroButtonEntityDescription[OneRFIDSmartFeeder](
            key="sound_off",
            translation_key="sound_off",
            set_fn=lambda device: device.set_sound_off(),
            name="Turn Off Sound"
        ),
        PetLibroButtonEntityDescription[OneRFIDSmartFeeder](
            key="desiccant_reset",
            translation_key="desiccant_reset",
            set_fn=lambda device: device.set_desiccant_reset(),
            name="Desiccant Reset"
        )
    ],
    PolarWetFoodFeeder: [
        PetLibroButtonEntityDescription[PolarWetFoodFeeder](
            key="ring_bell",
            translation_key="ring_bell",
            set_fn=lambda device: device.feed_audio(),
            name="Ring Bell"
        ),
        PetLibroButtonEntityDescription[PolarWetFoodFeeder](
            key="rotate_food_bowl",
            translation_key="rotate_food_bowl",
            set_fn=lambda device: device.rotate_food_bowl(),
            name="Rotate Food Bowl"
        ),
        PetLibroButtonEntityDescription[PolarWetFoodFeeder](
            key="reposition_schedule",
            translation_key="reposition_schedule",
            set_fn=lambda device: device.reposition_schedule(),
            name="Reposition the schedule"
        ),
        PetLibroButtonEntityDescription[PolarWetFoodFeeder](
            key="light_on",
            translation_key="light_on",
            set_fn=lambda device: device.set_light_on(),
            name="Turn On Indicator"
        ),
        PetLibroButtonEntityDescription[PolarWetFoodFeeder](
            key="light_off",
            translation_key="light_off",
            set_fn=lambda device: device.set_light_off(),
            name="Turn Off Indicator"
        ),
    ],
    SpaceSmartFeeder: [
        PetLibroButtonEntityDescription[SpaceSmartFeeder](
            key="manual_feed",
            translation_key="manual_feed",
            set_fn=lambda device: device.set_manual_feed(),
            name="Manual Feed"
        ),
        PetLibroButtonEntityDescription[SpaceSmartFeeder](
            key="enable_feeding_plan",
            translation_key="enable_feeding_plan",
            set_fn=lambda device: device.set_feeding_plan(True),
            name="Enable Feeding Plan"
        ),
        PetLibroButtonEntityDescription[SpaceSmartFeeder](
            key="disable_feeding_plan",
            translation_key="disable_feeding_plan",
            set_fn=lambda device: device.set_feeding_plan(False),
            name="Disable Feeding Plan"
        ),
        PetLibroButtonEntityDescription[SpaceSmartFeeder](
            key="sound_on",
            translation_key="sound_on",
            set_fn=lambda device: device.set_sound_on(),
            name="Turn On Sound"
        ),
        PetLibroButtonEntityDescription[SpaceSmartFeeder](
            key="sound_off",
            translation_key="sound_off",
            set_fn=lambda device: device.set_sound_off(),
            name="Turn Off Sound"
        ),
        PetLibroButtonEntityDescription[SpaceSmartFeeder](
            key="light_on",
            translation_key="light_on",
            set_fn=lambda device: device.set_light_on(),
            name="Turn On Indicator"
        ),
        PetLibroButtonEntityDescription[SpaceSmartFeeder](
            key="light_off",
            translation_key="light_off",
            set_fn=lambda device: device.set_light_off(),
            name="Turn Off Indicator"
        ),
        PetLibroButtonEntityDescription[SpaceSmartFeeder](
            key="sleep_on",
            translation_key="sleep_on",
            set_fn=lambda device: device.set_sleep_on(),
            name="Turn On Sleep Mode"
        ),
        PetLibroButtonEntityDescription[SpaceSmartFeeder](
            key="sleep_off",
            translation_key="sleep_off",
            set_fn=lambda device: device.set_sleep_off(),
            name="Turn Off Sleep Mode"
        ),
    ],
    DockstreamSmartFountain: [
        PetLibroButtonEntityDescription[DockstreamSmartFountain](
            key="light_on",
            translation_key="light_on",
            set_fn=lambda device: device.set_light_on(),
            name="Turn On Indicator"
        ),
        PetLibroButtonEntityDescription[DockstreamSmartFountain](
            key="light_off",
            translation_key="light_off",
            set_fn=lambda device: device.set_light_off(),
            name="Turn Off Indicator"
        ),
        PetLibroButtonEntityDescription[DockstreamSmartFountain](
            key="cleaning_reset",
            translation_key="cleaning_reset",
            set_fn=lambda device: device.set_cleaning_reset(),
            name="Cleaning Reset"
        ),
        PetLibroButtonEntityDescription[DockstreamSmartFountain](
            key="filter_reset",
            translation_key="filter_reset",
            set_fn=lambda device: device.set_filter_reset(),
            name="Filter Reset"
        )
    ],
    DockstreamSmartRFIDFountain: [
        PetLibroButtonEntityDescription[DockstreamSmartRFIDFountain](
            key="light_on",
            translation_key="light_on",
            set_fn=lambda device: device.set_light_on(),
            name="Turn On Indicator"
        ),
        PetLibroButtonEntityDescription[DockstreamSmartRFIDFountain](
            key="light_off",
            translation_key="light_off",
            set_fn=lambda device: device.set_light_off(),
            name="Turn Off Indicator"
        ),
        PetLibroButtonEntityDescription[DockstreamSmartRFIDFountain](
            key="cleaning_reset",
            translation_key="cleaning_reset",
            set_fn=lambda device: device.set_cleaning_reset(),
            name="Cleaning Reset"
        ),
        PetLibroButtonEntityDescription[DockstreamSmartRFIDFountain](
            key="filter_reset",
            translation_key="filter_reset",
            set_fn=lambda device: device.set_filter_reset(),
            name="Filter Reset"
        )
    ],
    Dockstream2SmartCordlessFountain: [
        PetLibroButtonEntityDescription[Dockstream2SmartCordlessFountain](
            key="light_on",
            translation_key="light_on",
            set_fn=lambda device: device.set_light_on(),
            name="Turn On Indicator"
        ),
        PetLibroButtonEntityDescription[Dockstream2SmartCordlessFountain](
            key="light_off",
            translation_key="light_off",
            set_fn=lambda device: device.set_light_off(),
            name="Turn Off Indicator"
        ),
        PetLibroButtonEntityDescription[Dockstream2SmartCordlessFountain](
            key="cleaning_reset",
            translation_key="cleaning_reset",
            set_fn=lambda device: device.set_cleaning_reset(),
            name="Cleaning Reset"
        ),
        PetLibroButtonEntityDescription[Dockstream2SmartCordlessFountain](
            key="filter_reset",
            translation_key="filter_reset",
            set_fn=lambda device: device.set_filter_reset(),
            name="Filter Reset"
        )
    ],
    Dockstream2SmartFountain: [
        PetLibroButtonEntityDescription[Dockstream2SmartFountain](
            key="light_on",
            translation_key="light_on",
            set_fn=lambda device: device.set_light_on(),
            name="Turn On Indicator"
        ),
        PetLibroButtonEntityDescription[Dockstream2SmartFountain](
            key="light_off",
            translation_key="light_off",
            set_fn=lambda device: device.set_light_off(),
            name="Turn Off Indicator"
        ),
        PetLibroButtonEntityDescription[Dockstream2SmartFountain](
            key="cleaning_reset",
            translation_key="cleaning_reset",
            set_fn=lambda device: device.set_cleaning_reset(),
            name="Cleaning Reset"
        ),
        PetLibroButtonEntityDescription[Dockstream2SmartFountain](
            key="filter_reset",
            translation_key="filter_reset",
            set_fn=lambda device: device.set_filter_reset(),
            name="Filter Reset"
        )
    ],
    LumaSmartLitterBox: [
        PetLibroButtonEntityDescription[LumaSmartLitterBox](
            key="trigger_clean",
            translation_key="trigger_clean",
            set_fn=lambda device: device.trigger_manual_clean(),
            name="Start Clean Cycle",
        ),
        PetLibroButtonEntityDescription[LumaSmartLitterBox](
            key="trigger_empty_waste",
            translation_key="trigger_empty_waste",
            set_fn=lambda device: device.trigger_empty_waste(),
            name="Empty Waste Bin",
        ),
        PetLibroButtonEntityDescription[LumaSmartLitterBox](
            key="trigger_level_litter",
            translation_key="trigger_level_litter",
            set_fn=lambda device: device.trigger_level_litter(),
            name="Level Litter",
        ),
        PetLibroButtonEntityDescription[LumaSmartLitterBox](
            key="trigger_stop_action",
            translation_key="trigger_stop_action",
            set_fn=lambda device: device.trigger_stop_action(),
            name="Stop Current Action",
        ),
        PetLibroButtonEntityDescription[LumaSmartLitterBox](
            key="trigger_open_door",
            translation_key="trigger_open_door",
            set_fn=lambda device: device.trigger_open_door(),
            name="Open Door",
        ),
        PetLibroButtonEntityDescription[LumaSmartLitterBox](
            key="trigger_close_door",
            translation_key="trigger_close_door",
            set_fn=lambda device: device.trigger_close_door(),
            name="Close Door",
        ),
        PetLibroButtonEntityDescription[LumaSmartLitterBox](
            key="trigger_vacuum",
            translation_key="trigger_vacuum",
            set_fn=lambda device: device.trigger_vacuum(),
            name="Run Air Purifier",
        ),
    ],
}


class PetLibroButtonEntity(PetLibroEntity[_DeviceT], ButtonEntity):
    """PETLIBRO button entity."""
    entity_description: PetLibroButtonEntityDescription[_DeviceT]

    @property
    def available(self) -> bool:
        """Check if the device is available."""
        return getattr(self.device, 'online', False)

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.debug("Pressing button: %s for device %s", self.entity_description.name, self.device.name)
        _LOGGER.debug("Available methods for device %s: %s", self.device.name, dir(self.device))

        try:
            await self.entity_description.set_fn(self.device)
            await self.device.refresh()
            _LOGGER.debug("Successfully pressed button: %s", self.entity_description.name)
        except Exception as e:
            _LOGGER.error(
                f"Error pressing button {self.entity_description.name} for device {self.device.name}: {e}",
                exc_info=True
            )

class FeedingPlanButtonEntity(PetLibroEntity[_DeviceT], ButtonEntity):
    """Button that acts on whichever feeding plan is currently selected in
    the companion select entity.

    action_fn:  async callable(device, plan_id) — the API action to perform.
    select_key: unique_id suffix of the select entity to read from,
                either 'feeding_plan_select' or 'feeding_plan_today_select'.
    """

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, device, hub, key: str, name: str, icon: str,
                 action_fn, select_key: str) -> None:
        desc = PetLibroEntityDescription(key=key, name=name)
        super().__init__(device, hub, desc)
        self._attr_unique_id = f"{device.serial}-{key}"
        self._attr_icon = icon
        self._action_fn = action_fn
        self._select_key = select_key

    @property
    def available(self) -> bool:
        """Check if the device is available."""
        return getattr(self.device, 'online', False)

    def _get_plan_id(self) -> int:
        """Read the currently selected plan ID from the companion select entity."""
        ent_reg = er.async_get(self.hass)
        unique_id = f"{self.device.serial}-{self._select_key}"
        entity_id = ent_reg.async_get_entity_id("select", DOMAIN, unique_id)

        if not entity_id:
            raise HomeAssistantError(
                f"No feeding plan selector found for {self.device.name}. "
                "Make sure the integration has loaded correctly."
            )

        state = self.hass.states.get(entity_id)
        if not state or state.state in ("unknown", "unavailable", "No plans", "No plans today"):
            raise HomeAssistantError(
                f"No plan selected on {self.device.name}. "
                "Select a plan from the feeding plan dropdown first."
            )

        match = re.search(r"-\s*(\d+)\s*$", state.state)
        if not match:
            raise HomeAssistantError(
                f"Could not extract a plan ID from '{state.state}'."
            )

        return int(match.group(1))

    async def async_press(self) -> None:
        """Handle button press — act on the currently selected plan."""
        try:
            plan_id = self._get_plan_id()
            await self._action_fn(self.device, plan_id)
            await self.device.refresh()
            _LOGGER.debug(
                "Feeding plan button '%s' pressed for plan %d on %s",
                self.name, plan_id, self.device.name,
            )
        except HomeAssistantError:
            raise
        except Exception as e:
            _LOGGER.error(
                "Error pressing feeding plan button '%s' for device %s: %s",
                self.name, self.device.name, e, exc_info=True,
            )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PETLIBRO buttons using config entry."""
    hub: PetLibroHub = hass.data[DOMAIN].get(entry.entry_id)

    if not hub:
        _LOGGER.error("Hub not found for entry: %s", entry.entry_id)
        return

    if not hub.devices:
        _LOGGER.warning("No devices found in hub during button setup.")
        return

    _LOGGER.debug("Hub data: %s", hub)
    devices = hub.devices
    _LOGGER.debug("Devices in hub: %s", devices)

    # Standard buttons from the device map
    entities = [
        PetLibroButtonEntity(device, hub, description)
        for device in devices.values()
        for device_type, entity_descriptions in DEVICE_BUTTON_MAP.items()
        if isinstance(device, device_type)
        for description in entity_descriptions
    ]

    # Feeding plan action buttons for dry feeders
    for device in devices.values():
        if hasattr(device, "feeding_plan_data"):
            entities.extend([
                FeedingPlanButtonEntity(
                    device, hub,
                    key="feeding_plan_enable",
                    name="Enable Selected Plan",
                    icon="mdi:calendar-check",
                    action_fn=lambda d, pid: d.api.feeding_plan_toggle(
                        d.serial,
                        {**d.feeding_plan_data.get(str(pid), {}), "id": pid, "enable": True},
                    ),
                    select_key="feeding_plan_select",
                ),
                FeedingPlanButtonEntity(
                    device, hub,
                    key="feeding_plan_disable",
                    name="Disable Selected Plan",
                    icon="mdi:calendar-remove",
                    action_fn=lambda d, pid: d.api.feeding_plan_toggle(
                        d.serial,
                        {**d.feeding_plan_data.get(str(pid), {}), "id": pid, "enable": False},
                    ),
                    select_key="feeding_plan_select",
                ),
                FeedingPlanButtonEntity(
                    device, hub,
                    key="feeding_plan_delete",
                    name="Delete Selected Plan",
                    icon="mdi:calendar-minus",
                    action_fn=lambda d, pid: d.api.feeding_plan_delete(d.serial, pid),
                    select_key="feeding_plan_select",
                ),
                FeedingPlanButtonEntity(
                    device, hub,
                    key="feeding_plan_skip_today",
                    name="Skip Selected Plan Today",
                    icon="mdi:calendar-today",
                    action_fn=lambda d, pid: d.api.feeding_plan_today_skip(d.serial, pid, skip=True),
                    select_key="feeding_plan_today_select",
                ),
                FeedingPlanButtonEntity(
                    device, hub,
                    key="feeding_plan_unskip_today",
                    name="Un-skip Selected Plan Today",
                    icon="mdi:calendar-today",
                    action_fn=lambda d, pid: d.api.feeding_plan_today_skip(d.serial, pid, skip=False),
                    select_key="feeding_plan_today_select",
                ),
            ])

    if not entities:
        _LOGGER.warning("No buttons added, entities list is empty!")
    else:
        _LOGGER.debug("Adding %d PetLibro buttons", len(entities))
        for entity in entities:
            _LOGGER.debug("Adding button entity: %s for device %s", entity.entity_description.name if hasattr(entity, 'entity_description') else entity.name, entity.device.name)

        async_add_entities(entities)