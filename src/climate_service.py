"""
Virtual Climate ECU - Assignment 2

Provides ClimateService.
"""

import asyncio
import logging

from someipy import (
    MessageType,
    Method,
    MethodResult,
    ReturnCode,
    ServerServiceInstance,
    ServiceBuilder,
    TransportLayerProtocol,
    connect_to_someipy_daemon,
)

from someipy.someipy_logging import set_someipy_log_level

from src.climate_interface import (
    CLIMATE_SERVICE_ID,
    CLIMATE_INSTANCE_ID,
    CLIMATE_PROVIDER_PORT,
    INTERFACE_IP,
    CLIMATE_MAJOR_VERSION,
    GET_CABIN_TEMPERATURE_METHOD_ID,
    SET_TARGET_TEMPERATURE_METHOD_ID,
    CABIN_TEMPERATURE_CHANGED_EVENT_ID,
    CLIMATE_EVENTGROUP_ID,
    TemperaturePayload,
    get_cabin_temperature_method,
    set_target_temperature_method,
    climate_eventgroup,
)


# ============================================================
# CLIMATE DATA
# ============================================================

current_cabin_temperature = 250
target_temperature = 220

MIN_TARGET_TEMPERATURE = 160
MAX_TARGET_TEMPERATURE = 300


# ============================================================
# METHOD 1: GET CABIN TEMPERATURE
# ============================================================

async def get_cabin_temperature_handler(
    input_data,
    client_address,
):

    print("\nGetCabinTemperature request received")

    result = MethodResult()

    result.message_type = MessageType.RESPONSE
    result.return_code = ReturnCode.E_OK

    result.payload = TemperaturePayload(
        current_cabin_temperature
    ).serialize()

    print(
        f"Cabin temperature: "
        f"{current_cabin_temperature / 10:.1f} °C"
    )

    return result


# ============================================================
# METHOD 2: SET TARGET TEMPERATURE
# ============================================================

async def set_target_temperature_handler(
    input_data,
    client_address,
):

    global target_temperature

    print("\nSetTargetTemperature request received")

    result = MethodResult()

    result.message_type = MessageType.RESPONSE

    if len(input_data) != 2:

        result.return_code = ReturnCode.E_MALFORMED_MESSAGE
        result.payload = bytes([1])

        print("Invalid temperature payload length")

        return result

    requested_temperature = (
        TemperaturePayload().deserialize(input_data)
    ).temperature.value

    print(
        f"Requested target temperature: "
        f"{requested_temperature / 10:.1f} °C"
    )

    if (
        MIN_TARGET_TEMPERATURE
        <= requested_temperature
        <= MAX_TARGET_TEMPERATURE
    ):

        target_temperature = requested_temperature

        result.return_code = ReturnCode.E_OK
        result.payload = bytes([0])

        print("Target temperature ACCEPTED")

    else:

        result.return_code = ReturnCode.E_OK
        result.payload = bytes([1])

        print("Target temperature INVALID")

    return result


# ============================================================
# BUILD CLIMATE SERVICE
# ============================================================

def build_climate_service():

    get_temperature = Method(
        id=GET_CABIN_TEMPERATURE_METHOD_ID,
        protocol=TransportLayerProtocol.UDP,
        method_handler=get_cabin_temperature_handler,
    )

    set_temperature = Method(
        id=SET_TARGET_TEMPERATURE_METHOD_ID,
        protocol=TransportLayerProtocol.UDP,
        method_handler=set_target_temperature_handler,
    )

    return (
        ServiceBuilder()
        .with_service_id(CLIMATE_SERVICE_ID)
        .with_major_version(CLIMATE_MAJOR_VERSION)
        .with_method(get_temperature)
        .with_method(set_temperature)
        .with_eventgroup(climate_eventgroup)
        .build()
    )


# ============================================================
# SIMULATE CABIN TEMPERATURE
# ============================================================

async def simulate_cabin_temperature(service_instance):

    global current_cabin_temperature

    while True:

        if current_cabin_temperature < target_temperature:

            current_cabin_temperature += 10

        elif current_cabin_temperature > target_temperature:

            current_cabin_temperature -= 10

        print("\n========================================")

        print(
            f"Cabin temperature: "
            f"{current_cabin_temperature / 10:.1f} °C"
        )

        print(
            f"Target temperature: "
            f"{target_temperature / 10:.1f} °C"
        )

        event_payload = TemperaturePayload(
            current_cabin_temperature
        ).serialize()

        service_instance.send_event(
            CLIMATE_EVENTGROUP_ID,
            CABIN_TEMPERATURE_CHANGED_EVENT_ID,
            event_payload,
        )

        print("CabinTemperatureChanged event sent")

        await asyncio.sleep(5)


# ============================================================
# MAIN FUNCTION
# ============================================================

async def main():

    set_someipy_log_level(logging.INFO)

    print("=" * 55)
    print("VIRTUAL CLIMATE ECU")
    print("ClimateService Provider")
    print("=" * 55)

    print(f"Service ID : 0x{CLIMATE_SERVICE_ID:04X}")
    print(f"Instance ID: 0x{CLIMATE_INSTANCE_ID:04X}")

    print(
        f"Provider endpoint: "
        f"{INTERFACE_IP}:{CLIMATE_PROVIDER_PORT}"
    )

    print("\nConnecting to SOME/IP daemon...")

    daemon = await connect_to_someipy_daemon()

    print("Connected to SOME/IP daemon")

    climate_service = build_climate_service()

    provider_instance = ServerServiceInstance(
        daemon=daemon,
        service=climate_service,
        instance_id=CLIMATE_INSTANCE_ID,
        endpoint_ip=INTERFACE_IP,
        endpoint_port=CLIMATE_PROVIDER_PORT,
        ttl=5,
        cyclic_offer_delay_ms=2000,
    )

    print("\nOffering ClimateService...")

    await provider_instance.start_offer()

    print("ClimateService is being offered")

    temperature_task = asyncio.create_task(
        simulate_cabin_temperature(provider_instance)
    )

    try:

        await asyncio.Future()

    finally:

        temperature_task.cancel()

        try:
            await temperature_task
        except asyncio.CancelledError:
            pass

        await provider_instance.stop_offer()

        await daemon.disconnect_from_daemon()


if __name__ == "__main__":

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("\nClimate ECU stopped")
