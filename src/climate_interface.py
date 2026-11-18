"""
Climate Service Interface - Assignment 2
"""

from dataclasses import dataclass

from someipy import (
    Event,
    EventGroup,
    Method,
    ServiceBuilder,
    TransportLayerProtocol,
)

from someipy.serialization import SomeIpPayload, Sint16


# ============================================================
# CLIMATE SERVICE CONFIGURATION
# ============================================================

CLIMATE_SERVICE_ID = 0x2234
CLIMATE_INSTANCE_ID = 0x0001
CLIMATE_MAJOR_VERSION = 1

INTERFACE_IP = "127.0.0.1"
CLIMATE_PROVIDER_PORT = 3001
CLIMATE_CONSUMER_PORT = 3003


# ============================================================
# METHOD IDs
# ============================================================

GET_CABIN_TEMPERATURE_METHOD_ID = 0x0001
SET_TARGET_TEMPERATURE_METHOD_ID = 0x0002


# ============================================================
# EVENT IDs
# ============================================================

CABIN_TEMPERATURE_CHANGED_EVENT_ID = 0x8001
CLIMATE_EVENTGROUP_ID = 0x0001


# ============================================================
# TEMPERATURE PAYLOAD
# ============================================================

@dataclass
class TemperaturePayload(SomeIpPayload):

    temperature: Sint16

    def __init__(self, temperature: int = 0):

        self.temperature = Sint16(temperature)


# ============================================================
# METHOD DEFINITIONS
# ============================================================

get_cabin_temperature_method = Method(
    id=GET_CABIN_TEMPERATURE_METHOD_ID,
    protocol=TransportLayerProtocol.UDP,
)

set_target_temperature_method = Method(
    id=SET_TARGET_TEMPERATURE_METHOD_ID,
    protocol=TransportLayerProtocol.UDP,
)


# ============================================================
# EVENT DEFINITIONS
# ============================================================

cabin_temperature_changed_event = Event(
    id=CABIN_TEMPERATURE_CHANGED_EVENT_ID,
    protocol=TransportLayerProtocol.UDP,
)


climate_eventgroup = EventGroup(
    id=CLIMATE_EVENTGROUP_ID,
    events=[cabin_temperature_changed_event],
)


# ============================================================
# CLIMATE SERVICE DEFINITION
# ============================================================

climate_service = (
    ServiceBuilder()
    .with_service_id(CLIMATE_SERVICE_ID)
    .with_major_version(CLIMATE_MAJOR_VERSION)
    .with_method(get_cabin_temperature_method)
    .with_method(set_target_temperature_method)
    .with_eventgroup(climate_eventgroup)
    .build()
)
