"""Binary Sensors for status entities."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import COORDINATOR, DOMAIN

from .span_panel import SpanPanel
from .span_panel_hardware_status import SpanPanelHardwareStatus
from .util import panel_to_device_info

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class SpanPanelRequiredKeysMixin:
    value_fn: Callable[[SpanPanelHardwareStatus], str]


@dataclass(frozen=True)
class SpanPanelBinarySensorEntityDescription(
    BinarySensorEntityDescription, SpanPanelRequiredKeysMixin
):
    """Describes an SpanPanelCircuits sensor entity."""


BINARY_SENSORS = (
    SpanPanelBinarySensorEntityDescription(
        key="doorState",
        name="Door State",
        device_class=BinarySensorDeviceClass.TAMPER,
        value_fn=lambda status_data: not status_data.is_door_closed,
    ),
    SpanPanelBinarySensorEntityDescription(
        key="eth0Link",
        name="Ethernet Link",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda status_data: status_data.is_ethernet_connected,
    ),
    SpanPanelBinarySensorEntityDescription(
        key="wlanLink",
        name="Wi-Fi Link",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda status_data: status_data.is_wifi_connected,
    ),
    SpanPanelBinarySensorEntityDescription(
        key="wwanLink",
        name="Cellular Link",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda status_data: status_data.is_cellular_connected,
    ),
)


class SpanPanelBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary Sensor status entity."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        description: SpanPanelBinarySensorEntityDescription,
    ) -> None:
        """Initialize Span Panel Circuit entity."""
        span_panel: SpanPanel = coordinator.data

        self.entity_description = description
        self._attr_name = f"{description.name}"
        self._attr_unique_id = (
            f"span_{span_panel.status.serial_number}_{description.key}"
        )
        self._attr_device_info = panel_to_device_info(span_panel)

        _LOGGER.debug("CREATE BINSENSOR [%s]" % self._attr_name)
        super().__init__(coordinator)

    @property
    def is_on(self):
        """Return the status of the sensor."""
        _LOGGER.debug("BINSENSOR [%s] IS_ON" % self._attr_name)
        span_panel: SpanPanel = self.coordinator.data
        return self.entity_description.value_fn(span_panel.status)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up status sensor platform."""

    _LOGGER.debug("ASYNC SETUP ENTRY BINARYSENSOR")

    data: dict = hass.data[DOMAIN][config_entry.entry_id]
    coordinator: DataUpdateCoordinator = data[COORDINATOR]

    entities: list[SpanPanelBinarySensor] = []

    for description in BINARY_SENSORS:
        entities.append(SpanPanelBinarySensor(coordinator, description))

    async_add_entities(entities)
