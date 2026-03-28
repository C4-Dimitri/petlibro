"""PETLIBRO feeding plan services."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN
from .devices.feeders.feeder import Feeder

_LOGGER = logging.getLogger(__name__)

# Service names
SERVICE_ENABLE_FEEDING_PLAN         = "enable_feeding_plan"
SERVICE_DISABLE_FEEDING_PLAN        = "disable_feeding_plan"
SERVICE_DELETE_FEEDING_PLAN         = "delete_feeding_plan"
SERVICE_EDIT_FEEDING_PLAN           = "edit_feeding_plan"
SERVICE_ADD_FEEDING_PLAN            = "add_feeding_plan"
SERVICE_ENABLE_TODAY_FEEDING_PLAN   = "enable_today_feeding_plan"
SERVICE_DISABLE_TODAY_FEEDING_PLAN  = "disable_today_feeding_plan"

# Shared field keys
_DEVICE_ID  = "device_id"
_PLAN_ID    = "plan_id"
_TIME       = "time"
_PORTIONS   = "portions"
_LABEL      = "label"
_DAYS       = "days"
_SOUND      = "sound"


def _get_feeder(hass: HomeAssistant, device_id: str) -> Feeder:
    """Resolve a HA device_id to a PetLibro Feeder instance.

    Raises ServiceValidationError if the device is not found or is not a
    dry-food feeder (i.e. does not have feeding_plan_data).
    """
    dev_reg = dr.async_get(hass)
    device_entry = dev_reg.async_get(device_id)
    if not device_entry:
        raise ServiceValidationError(f"Device {device_id} not found.")

    # Find the serial number from the device identifiers
    serial = next(
        (identifier[1] for identifier in device_entry.identifiers if identifier[0] == DOMAIN),
        None,
    )
    if not serial:
        raise ServiceValidationError(
            f"Device {device_id} is not a PETLIBRO device."
        )

    # Walk every hub entry to find the matching device
    for entry_id, hub in hass.data.get(DOMAIN, {}).items():
        device = hub.devices.get(serial)
        if device is not None:
            if not isinstance(device, Feeder) or not hasattr(device, "feeding_plan_data"):
                raise ServiceValidationError(
                    f"{device.name} does not support feeding plan services. "
                    "Only dry food feeders are supported."
                )
            return device

    raise ServiceValidationError(
        f"No loaded PetLibro device found for serial {serial}."
    )


def _build_plan_payload(
    device: Feeder,
    *,
    plan_id: int | None = None,
    time_str: str | None = None,
    portions: int | None = None,
    label: str | None = None,
    days: list[str] | None = None,
    sound: bool | None = None,
    enable: bool | None = None,
) -> dict[str, Any]:
    """Build the feedingPlan payload for save/update API calls.

    When editing, we start from the existing plan data so that any field
    the caller didn't supply keeps its current value.
    """
    base: dict[str, Any] = {}

    if plan_id is not None:
        existing = device.feeding_plan_data.get(str(plan_id), {})
        base.update(existing)
        base["id"] = plan_id

    # Override with any supplied values
    if time_str is not None:
        base["executionTime"] = time_str
    if portions is not None:
        base["grainNum"] = portions
    if label is not None:
        base["label"] = label
    if days is not None:
        # API expects a Python-repr list string e.g. "[1, 3, 5]"
        base["repeatDay"] = str([int(d) for d in days])
    if sound is not None:
        base["enableAudio"] = sound
    if enable is not None:
        base["enable"] = enable

    return base


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register all PETLIBRO feeding plan services."""
    if hass.services.has_service(DOMAIN, SERVICE_ENABLE_FEEDING_PLAN):
        return  # Already registered

    # ------------------------------------------------------------------
    # enable_feeding_plan
    # ------------------------------------------------------------------
    async def handle_enable_feeding_plan(call: ServiceCall) -> None:
        device = _get_feeder(hass, call.data[_DEVICE_ID])
        plan_id: int = call.data[_PLAN_ID]

        payload = _build_plan_payload(device, plan_id=plan_id, enable=True)
        await device.api.feeding_plan_update(device.serial, payload)
        await device.refresh()
        _LOGGER.debug("Enabled feeding plan %d on %s", plan_id, device.name)

    hass.services.async_register(DOMAIN, SERVICE_ENABLE_FEEDING_PLAN, handle_enable_feeding_plan)

    # ------------------------------------------------------------------
    # disable_feeding_plan
    # ------------------------------------------------------------------
    async def handle_disable_feeding_plan(call: ServiceCall) -> None:
        device = _get_feeder(hass, call.data[_DEVICE_ID])
        plan_id: int = call.data[_PLAN_ID]

        payload = _build_plan_payload(device, plan_id=plan_id, enable=False)
        await device.api.feeding_plan_update(device.serial, payload)
        await device.refresh()
        _LOGGER.debug("Disabled feeding plan %d on %s", plan_id, device.name)

    hass.services.async_register(DOMAIN, SERVICE_DISABLE_FEEDING_PLAN, handle_disable_feeding_plan)

    # ------------------------------------------------------------------
    # delete_feeding_plan
    # ------------------------------------------------------------------
    async def handle_delete_feeding_plan(call: ServiceCall) -> None:
        device = _get_feeder(hass, call.data[_DEVICE_ID])
        plan_id: int = call.data[_PLAN_ID]

        await device.api.feeding_plan_delete(device.serial, plan_id)
        await device.refresh()
        _LOGGER.debug("Deleted feeding plan %d on %s", plan_id, device.name)

    hass.services.async_register(DOMAIN, SERVICE_DELETE_FEEDING_PLAN, handle_delete_feeding_plan)

    # ------------------------------------------------------------------
    # edit_feeding_plan
    # ------------------------------------------------------------------
    async def handle_edit_feeding_plan(call: ServiceCall) -> None:
        device = _get_feeder(hass, call.data[_DEVICE_ID])
        plan_id: int = call.data[_PLAN_ID]

        existing = device.feeding_plan_data.get(str(plan_id))
        if not existing:
            raise ServiceValidationError(
                f"Plan ID {plan_id} not found on {device.name}. "
                "Check the feeder's sensor attributes for valid plan IDs."
            )

        payload = _build_plan_payload(
            device,
            plan_id=plan_id,
            time_str=call.data.get(_TIME),
            portions=call.data.get(_PORTIONS),
            label=call.data.get(_LABEL),
            days=call.data.get(_DAYS),
            sound=call.data.get(_SOUND),
        )
        await device.api.feeding_plan_update(device.serial, payload)
        await device.refresh()
        _LOGGER.debug("Edited feeding plan %d on %s", plan_id, device.name)

    hass.services.async_register(DOMAIN, SERVICE_EDIT_FEEDING_PLAN, handle_edit_feeding_plan)

    # ------------------------------------------------------------------
    # add_feeding_plan
    # ------------------------------------------------------------------
    async def handle_add_feeding_plan(call: ServiceCall) -> None:
        device = _get_feeder(hass, call.data[_DEVICE_ID])

        payload = _build_plan_payload(
            device,
            time_str=call.data[_TIME],
            portions=call.data[_PORTIONS],
            label=call.data.get(_LABEL, ""),
            days=call.data.get(_DAYS, []),
            sound=call.data.get(_SOUND, False),
            enable=True,
        )
        # No id in payload = new plan
        await device.api.feeding_plan_add(device.serial, payload)
        await device.refresh()
        _LOGGER.debug("Added new feeding plan on %s", device.name)

    hass.services.async_register(DOMAIN, SERVICE_ADD_FEEDING_PLAN, handle_add_feeding_plan)

    # ------------------------------------------------------------------
    # enable_today_feeding_plan  (un-skip today's event)
    # ------------------------------------------------------------------
    async def handle_enable_today_feeding_plan(call: ServiceCall) -> None:
        device = _get_feeder(hass, call.data[_DEVICE_ID])
        plan_id: int = call.data[_PLAN_ID]

        await device.api.feeding_plan_today_skip(device.serial, plan_id, skip=False)
        await device.refresh()
        _LOGGER.debug("Un-skipped today's feeding plan %d on %s", plan_id, device.name)

    hass.services.async_register(
        DOMAIN, SERVICE_ENABLE_TODAY_FEEDING_PLAN, handle_enable_today_feeding_plan
    )

    # ------------------------------------------------------------------
    # disable_today_feeding_plan  (skip today's event)
    # ------------------------------------------------------------------
    async def handle_disable_today_feeding_plan(call: ServiceCall) -> None:
        device = _get_feeder(hass, call.data[_DEVICE_ID])
        plan_id: int = call.data[_PLAN_ID]

        await device.api.feeding_plan_today_skip(device.serial, plan_id, skip=True)
        await device.refresh()
        _LOGGER.debug("Skipped today's feeding plan %d on %s", plan_id, device.name)

    hass.services.async_register(
        DOMAIN, SERVICE_DISABLE_TODAY_FEEDING_PLAN, handle_disable_today_feeding_plan
    )

    _LOGGER.debug("PETLIBRO feeding plan services registered.")


async def async_unload_services(hass: HomeAssistant) -> None:
    """Remove PETLIBRO feeding plan services when the integration is unloaded."""
    for service in (
        SERVICE_ENABLE_FEEDING_PLAN,
        SERVICE_DISABLE_FEEDING_PLAN,
        SERVICE_DELETE_FEEDING_PLAN,
        SERVICE_EDIT_FEEDING_PLAN,
        SERVICE_ADD_FEEDING_PLAN,
        SERVICE_ENABLE_TODAY_FEEDING_PLAN,
        SERVICE_DISABLE_TODAY_FEEDING_PLAN,
    ):
        hass.services.async_remove(DOMAIN, service)
    _LOGGER.debug("PETLIBRO feeding plan services removed.")