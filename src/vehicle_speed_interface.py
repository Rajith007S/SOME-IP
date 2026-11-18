from dataclasses import dataclass

from someipy import (
    Event,
    EventGroup,
    Method,
    ServiceBuilder,
    TransportLayerProtocol,
)

from someipy.serialization import SomeIpPayload, Uint8, Uint16


# ============================================================
# SERVICE IDENTIFICATION
# ============================================================

SERVICE_ID = 0x1234
INSTANCE_ID = 0x5678
MAJOR_VERSION = 1


# ============================================================
# METHOD IDENTIFICATION
# ============================================================

GET_SPEED_METHOD_ID = 0x0001
GET_VEHICLE_STATE_METHOD_ID = 0x0002


# ============================================================
# EVENT IDENTIFICATION
# ============================================================

SPEED_CHANGED_EVENT_ID = 0x8001
OVERSPEED_WARNING_EVENT_ID = 0x8002

SPEED_EVENTGROUP_ID = 0x0001
OVERSPEED_EVENTGROUP_ID = 0x0002


# ============================================================
# NETWORK CONFIGURATION
# ============================================================

INTERFACE_IP = "127.0.0.1"
PROVIDER_PORT = 3000
CONSUMER_PORT = 3002


# ============================================================
# PAYLOAD DEFINITIONS
# ============================================================

@dataclass
class SpeedPayload(SomeIpPayload):

    speed_kmph: Uint16

    def __init__(self, speed_kmph: int = 0):
        self.speed_kmph = Uint16(speed_kmph)


@dataclass
class VehicleStatePayload(SomeIpPayload):

    state: Uint8

    def __init__(self, state: int = 0):
        self.state = Uint8(state)


# ============================================================
# METHOD DEFINITIONS
# ============================================================

get_speed_method = Method(
    id=GET_SPEED_METHOD_ID,
    protocol=TransportLayerProtocol.UDP,
)

get_vehicle_state_method = Method(
    id=GET_VEHICLE_STATE_METHOD_ID,
    protocol=TransportLayerProtocol.UDP,
)


# ============================================================
# EVENT DEFINITIONS
# ============================================================

speed_changed_event = Event(
    id=SPEED_CHANGED_EVENT_ID,
    protocol=TransportLayerProtocol.UDP,
)

overspeed_warning_event = Event(
    id=OVERSPEED_WARNING_EVENT_ID,
    protocol=TransportLayerProtocol.UDP,
)


# ============================================================
# EVENT GROUPS
# ============================================================

speed_eventgroup = EventGroup(
    id=SPEED_EVENTGROUP_ID,
    events=[speed_changed_event],
)

overspeed_eventgroup = EventGroup(
    id=OVERSPEED_EVENTGROUP_ID,
    events=[overspeed_warning_event],
)


# ============================================================
# VEHICLE SPEED SERVICE
# ============================================================

vehicle_speed_service = (
    ServiceBuilder()
    .with_service_id(SERVICE_ID)
    .with_major_version(MAJOR_VERSION)
    .with_method(get_speed_method)
    .with_method(get_vehicle_state_method)
    .with_eventgroup(speed_eventgroup)
    .with_eventgroup(overspeed_eventgroup)
    .build()
)
