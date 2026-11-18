"""
Virtual Central Display ECU - Assignment 2.

Consumes:
1. VehicleSpeedService
2. ClimateService
"""

import asyncio
import logging

from someipy import (
    ClientServiceInstance,
    MessageType,
    ReturnCode,
    connect_to_someipy_daemon,
)

from someipy.someipy_logging import set_someipy_log_level

# Vehicle Service Interface
from src.vehicle_speed_interface import (
    SERVICE_ID,
    INSTANCE_ID,
    INTERFACE_IP,
    CONSUMER_PORT,
    GET_SPEED_METHOD_ID,
    GET_VEHICLE_STATE_METHOD_ID,
    SPEED_CHANGED_EVENT_ID,
    OVERSPEED_WARNING_EVENT_ID,
    SpeedPayload,
    VehicleStatePayload,
    speed_eventgroup,
    overspeed_eventgroup,
    vehicle_speed_service,
)

# Climate Service Interface
from src.climate_interface import (
    CLIMATE_SERVICE_ID,
    CLIMATE_INSTANCE_ID,
    CLIMATE_CONSUMER_PORT,
    GET_CABIN_TEMPERATURE_METHOD_ID,
    SET_TARGET_TEMPERATURE_METHOD_ID,
    CABIN_TEMPERATURE_CHANGED_EVENT_ID,
    TemperaturePayload,
    climate_eventgroup,
    climate_service,
)


# ============================================================
# VEHICLE EVENT CALLBACK
# ============================================================

def vehicle_event_callback(
    event_id: int,
    event_payload: bytes,
) -> None:

    try:

        message = SpeedPayload().deserialize(event_payload)

        speed = message.speed_kmph.value

        print()

        if event_id == SPEED_CHANGED_EVENT_ID:

            print("[CENTRAL DISPLAY] Vehicle Speed Updated")
            print(f"Speed: {speed} km/h")

        elif event_id == OVERSPEED_WARNING_EVENT_ID:

            print("!!! CENTRAL DISPLAY: OVERSPEED WARNING !!!")
            print(f"Current speed: {speed} km/h")

    except Exception as error:

        print(f"Vehicle event decoding failed: {error}")


# ============================================================
# CLIMATE EVENT CALLBACK
# ============================================================

def climate_event_callback(
    event_id: int,
    event_payload: bytes,
) -> None:

    try:

        if event_id == CABIN_TEMPERATURE_CHANGED_EVENT_ID:

            message = TemperaturePayload().deserialize(
                event_payload
            )

            temperature = message.temperature.value / 10

            print()
            print("[CENTRAL DISPLAY] Cabin Temperature Updated")
            print(f"Cabin Temperature: {temperature:.1f} °C")

    except Exception as error:

        print(f"Climate event decoding failed: {error}")


# ============================================================
# VEHICLE METHOD: GET SPEED
# ============================================================

async def call_get_speed(
    client_instance: ClientServiceInstance,
) -> None:

    while True:

        try:

            print("\n[DISPLAY] Calling GetSpeed...")

            result = await client_instance.call_method(
                GET_SPEED_METHOD_ID,
                b"",
            )

            if result.message_type == MessageType.RESPONSE:

                if result.return_code == ReturnCode.E_OK:

                    message = SpeedPayload().deserialize(
                        result.payload
                    )

                    print(
                        f"[DISPLAY] Vehicle Speed: "
                        f"{message.speed_kmph.value} km/h"
                    )

        except Exception as error:

            print(f"GetSpeed failed: {error}")

        await asyncio.sleep(5)


# ============================================================
# VEHICLE METHOD: GET VEHICLE STATE
# ============================================================

async def call_get_vehicle_state(
    client_instance: ClientServiceInstance,
) -> None:

    while True:

        try:

            print("\n[DISPLAY] Calling GetVehicleState...")

            result = await client_instance.call_method(
                GET_VEHICLE_STATE_METHOD_ID,
                b"",
            )

            if result.message_type == MessageType.RESPONSE:

                if result.return_code == ReturnCode.E_OK:

                    message = VehicleStatePayload().deserialize(
                        result.payload
                    )

                    state = message.state.value

                    if state == 0:
                        print("[DISPLAY] Vehicle State: STOPPED")

                    elif state == 1:
                        print("[DISPLAY] Vehicle State: MOVING")

                    else:
                        print(f"[DISPLAY] Unknown State: {state}")

        except Exception as error:

            print(f"GetVehicleState failed: {error}")

        await asyncio.sleep(5)


# ============================================================
# CLIMATE METHOD: GET CABIN TEMPERATURE
# ============================================================

async def call_get_cabin_temperature(
    client_instance: ClientServiceInstance,
) -> None:

    while True:

        try:

            print("\n[DISPLAY] Calling GetCabinTemperature...")

            result = await client_instance.call_method(
                GET_CABIN_TEMPERATURE_METHOD_ID,
                b"",
            )

            if result.message_type == MessageType.RESPONSE:

                if result.return_code == ReturnCode.E_OK:

                    message = TemperaturePayload().deserialize(
                        result.payload
                    )

                    temperature = message.temperature.value / 10

                    print(
                        f"[DISPLAY] Cabin Temperature: "
                        f"{temperature:.1f} °C"
                    )

        except Exception as error:

            print(f"GetCabinTemperature failed: {error}")

        await asyncio.sleep(5)


# ============================================================
# CLIMATE METHOD: SET TARGET TEMPERATURE
# ============================================================

async def set_target_temperature(
    client_instance: ClientServiceInstance,
    target_temperature: int,
) -> None:

    try:

        print(
            f"\n[DISPLAY] Setting target temperature: "
            f"{target_temperature / 10:.1f} °C"
        )

        payload = TemperaturePayload(
            target_temperature
        ).serialize()

        result = await client_instance.call_method(
            SET_TARGET_TEMPERATURE_METHOD_ID,
            payload,
        )

        if result.message_type == MessageType.RESPONSE:

            if result.return_code == ReturnCode.E_OK:

                if result.payload == bytes([0]):

                    print("[DISPLAY] Target Temperature ACCEPTED")

                elif result.payload == bytes([1]):

                    print("[DISPLAY] Target Temperature INVALID")

                else:

                    print(
                        f"[DISPLAY] Unexpected response: "
                        f"{result.payload.hex(' ')}"
                    )

    except Exception as error:

        print(f"SetTargetTemperature failed: {error}")


# ============================================================
# WAIT FOR SERVICE AVAILABILITY
# ============================================================

async def wait_for_service(
    client_instance: ClientServiceInstance,
    service_name: str,
) -> None:

    print(f"\nSearching for {service_name}...")

    while not await client_instance.is_available():

        print(f"{service_name} is not available yet")

        await asyncio.sleep(1)

    print(f"{service_name} is AVAILABLE")


# ============================================================
# MAIN FUNCTION
# ============================================================

async def main():

    set_someipy_log_level(logging.INFO)

    print("=" * 60)
    print("VIRTUAL CENTRAL DISPLAY ECU")
    print("SOME/IP Multi-Service Consumer")
    print("=" * 60)

    print("\nVehicleSpeedService ID: 0x1234")
    print("ClimateService ID     : 0x2234")

    print("\nConnecting to SOME/IP daemon...")

    daemon = await connect_to_someipy_daemon()

    print("Connected to SOME/IP daemon")

    # --------------------------------------------------------
    # CREATE VEHICLE CLIENT
    # --------------------------------------------------------

    vehicle_client = ClientServiceInstance(
        daemon=daemon,
        service=vehicle_speed_service,
        instance_id=INSTANCE_ID,
        endpoint_ip=INTERFACE_IP,
        endpoint_port=CONSUMER_PORT,
    )

    vehicle_client.register_callback(
        vehicle_event_callback
    )

    # --------------------------------------------------------
    # CREATE CLIMATE CLIENT
    # --------------------------------------------------------

    climate_client = ClientServiceInstance(
        daemon=daemon,
        service=climate_service,
        instance_id=CLIMATE_INSTANCE_ID,
        endpoint_ip=INTERFACE_IP,
        endpoint_port=CLIMATE_CONSUMER_PORT,
    )

    climate_client.register_callback(
        climate_event_callback
    )

    # --------------------------------------------------------
    # WAIT FOR BOTH SERVICES
    # --------------------------------------------------------

    await wait_for_service(
        vehicle_client,
        "VehicleSpeedService",
    )

    await wait_for_service(
        climate_client,
        "ClimateService",
    )

    # --------------------------------------------------------
    # SUBSCRIBE TO VEHICLE EVENTS
    # --------------------------------------------------------

    print("\nSubscribing to VehicleSpeedService events...")

    vehicle_client.subscribe_eventgroup(
        speed_eventgroup,
        5,
    )

    vehicle_client.subscribe_eventgroup(
        overspeed_eventgroup,
        5,
    )

    print("Vehicle event subscriptions requested")

    # --------------------------------------------------------
    # SUBSCRIBE TO CLIMATE EVENT
    # --------------------------------------------------------

    print("\nSubscribing to ClimateService events...")

    climate_client.subscribe_eventgroup(
        climate_eventgroup,
        5,
    )

    print("Climate event subscription requested")

    # --------------------------------------------------------
    # SET INITIAL TARGET TEMPERATURE
    # --------------------------------------------------------

    await set_target_temperature(
        climate_client,
        240,
    )

    # 240 = 24.0 degrees Celsius

    # --------------------------------------------------------
    # START METHOD TASKS
    # --------------------------------------------------------

    tasks = [

        asyncio.create_task(
            call_get_speed(vehicle_client)
        ),

        asyncio.create_task(
            call_get_vehicle_state(vehicle_client)
        ),

        asyncio.create_task(
            call_get_cabin_temperature(climate_client)
        ),

    ]

    try:

        await asyncio.Future()

    finally:

        print("\nStopping Central Display...")

        for task in tasks:

            task.cancel()

        for task in tasks:

            try:
                await task

            except asyncio.CancelledError:
                pass

        await daemon.disconnect_from_daemon()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        print("\nCentral Display stopped")
