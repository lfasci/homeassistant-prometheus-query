from __future__ import annotations

import logging
from typing import Optional, Union
import voluptuous as vol
import async_timeout
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from datetime import timedelta
from dataclasses import dataclass, field
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import (
    CONF_NAME,
    CONF_UNIT_OF_MEASUREMENT,
    STATE_UNKNOWN,
)
from homeassistant.components.sensor import (
    DEVICE_CLASSES_SCHEMA,
    STATE_CLASSES_SCHEMA,
)
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import slugify

CONF_PROMETHEUS_URL = "prometheus_url"
CONF_PROMETHEUS_QUERY = "prometheus_query"
CONF_STATE_CLASS = "state_class"
CONF_DEVICE_CLASS = "device_class"
CONF_UNIQUE_ID = "unique_id"
CONF_MONITORED_INSTANCES = "monitored_instances"
CONF_INSTANCE_NAME = "instance_name"
SCAN_INTERVAL = timedelta(seconds=20)

_LOGGER = logging.getLogger(__name__)

INSTANCE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_INSTANCE_NAME): str,
        vol.Optional(CONF_NAME): str,
    },
    extra=vol.ALLOW_EXTRA,
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_PROMETHEUS_URL): cv.string,
        vol.Required(CONF_PROMETHEUS_QUERY): cv.string,
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
        vol.Optional(CONF_STATE_CLASS): STATE_CLASSES_SCHEMA,
        vol.Optional(CONF_DEVICE_CLASS): DEVICE_CLASSES_SCHEMA,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
        vol.Optional(CONF_MONITORED_INSTANCES, default=[]): vol.All(
            cv.ensure_list, [INSTANCE_SCHEMA]
        ),
    }
)


@dataclass
class PromEntryData:
    url: str
    query: str
    name: str
    unit: str
    state_class: str
    device_class: str
    unique_id: str
    instance_mapper: dict[str, InstanceMapItem] = field(default_factory=dict)


@dataclass
class InstanceMapItem:
    instance_name: str
    entity_name: str


# def setup_platform(
async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: Optional[DiscoveryInfoType] = None,
):
    """Set up the sensor platform."""
    parse_instance_mapping = {
        (instance_name := raw_instance_item.get(CONF_INSTANCE_NAME)): InstanceMapItem(
            instance_name=instance_name,
            entity_name=raw_instance_item.get(CONF_NAME) or instance_name,
        )
        for raw_instance_item in config.get(CONF_MONITORED_INSTANCES)
    }

    prom_data = PromEntryData(
        url=str(config.get(CONF_PROMETHEUS_URL)) + "/api/v1/query",
        query=str(config.get(CONF_PROMETHEUS_QUERY)),
        name=str(config.get(CONF_NAME)),
        unit=str(config.get(CONF_UNIT_OF_MEASUREMENT)),
        state_class=str(config.get(CONF_STATE_CLASS)),
        device_class=str(config.get(CONF_DEVICE_CLASS)),
        unique_id=str(config.get(CONF_UNIQUE_ID)),
        instance_mapper=parse_instance_mapping,
    )

    _LOGGER.debug(f"prom_data is \n{prom_data}")

    coordinator = PrometheusQueryCoordinator(hass, prom_data)
    async_add_entities(
        construct_entities(coordinator, prom_data), update_before_add=True
    )


def construct_entities(
    coordinator: PrometheusQueryCoordinator, prom_data: PromEntryData
):
    entities_to_add: list[PrometheusQueryEntity] = []
    for instance_name, entity_mapping in prom_data.instance_mapper.items():
        entity_mapping.entity_name
        entities_to_add.append(
            PrometheusQueryEntity(coordinator, prom_data, instance_name)
        )
    if len(entities_to_add) <= 0:
        entities_to_add.append(
            PrometheusQuerySingleEntity(coordinator, prom_data, instance_name=None)
        )
    return entities_to_add


class PrometheusQueryCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass: HomeAssistant, prom_data: PromEntryData):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="My sensor",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=20),
        )
        self.data: dict[str, Union[float, int]]
        self.url = prom_data.url
        self.query = prom_data.query
        self.instance_mapper = prom_data.instance_mapper

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            session = async_get_clientsession(self.hass)
            async with async_timeout.timeout(10):
                async with session.get(self.url, params={"query": self.query}) as r:
                    raw_fetch_data: list[dict] = (
                        (await r.json()).get("data", {}).get("result", [])
                    )
                    # _LOGGER.debug(f"Raw fetched data is\n{raw_fetch_data}")
                    fetched_dict: dict[str, str] = {
                        fetched_item["metric"]["instance"]: fetched_item["value"][1]
                        for fetched_item in raw_fetch_data
                    }
                    parsed_data = fetched_dict
                    _LOGGER.debug(f"before filter={parsed_data}")
                    if len(self.instance_mapper) > 0:
                        # filter only used instance only when we use mapper
                        parsed_data = {
                            instance: value
                            for instance, value in fetched_dict.items()
                            if instance in self.instance_mapper
                        }
                    _LOGGER.debug(f"after filter={parsed_data}")
                    return parsed_data
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")


class PrometheusQueryEntity(CoordinatorEntity, SensorEntity):
    """Representation of a Sensor based on Prometheus"""

    def __init__(
        self,
        coordinator: PrometheusQueryCoordinator,
        prom_data: PromEntryData,
        instance_name: Optional[str] = None,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._instance_name = instance_name
        self._url = prom_data.url
        self._query = prom_data.query
        entity_map_item = prom_data.instance_mapper.get(instance_name, None)
        self._attr_name = (
            prom_data.name
            if entity_map_item is None
            else (entity_map_item.entity_name or prom_data.name)
        )
        self._state = None
        self._attr_native_unit_of_measurement = prom_data.unit
        self._attr_state_class = prom_data.state_class
        self._attr_device_class = prom_data.device_class
        self._attr_unique_id = slugify(
            (prom_data.unique_id or f"${prom_data.url}$${prom_data.query}")
            + (f"$${instance_name}" if instance_name is not None else "")
        )
        _LOGGER.debug(
            f"Created a PrometheusQueryEntity with instance_name={instance_name}"
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        fetched_data = self.coordinator.data
        if fetched_data is None:
            return
        self._attr_native_value = fetched_data.get(self._instance_name, STATE_UNKNOWN)
        self._attr_state = self._attr_native_value
        self.async_write_ha_state()

    # def update(self):
    #     """Fetch new state data for the sensor.
    #     This is the only method that should fetch new data for Home Assistant.
    #     """
    #     try:
    #         response = requests.get(self._url, params={"query": self._query})
    #         self._attr_native_value = STATE_UNKNOWN
    #         if response:
    #             results = response.json()["data"]["result"]
    #             _LOGGER.debug(f"result is {results}")
    #             if results:
    #                 self._attr_native_value = results[0]["value"][1]

    #         self._attr_state = self._attr_native_value

    #     except requests.exceptions.RequestException as e:
    #         _LOGGER.error("Error when retrieving update data")


class PrometheusQuerySingleEntity(PrometheusQueryEntity):
    """Representation of a Sensor based on Prometheus"""

    def __init__(
        self,
        coordinator: PrometheusQueryCoordinator,
        prom_data: PromEntryData,
        instance_name: Optional[str] = None,
    ):
        super().__init__(coordinator, prom_data, instance_name)
        self._attr_name = prom_data.name
        _LOGGER.debug("Created a PrometheusQuerySingleEntity")

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        fetched_values = list(self.coordinator.data.values())
        self._attr_native_value = (
            STATE_UNKNOWN if len(fetched_values) <= 0 else fetched_values[0]
        )
        self._attr_state = self._attr_native_value
        self.async_write_ha_state()
