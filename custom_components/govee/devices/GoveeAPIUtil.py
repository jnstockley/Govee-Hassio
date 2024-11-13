import logging

import httpx

log = logging.getLogger()


BASE_URL = "https://openapi.api.govee.com"


async def get_device_state(api_key: str, sku: str, device: str):
    try:
        headers = {'Govee-API-Key': api_key, 'Content-Type': 'application/json'}
        body = {"requestId": "uuid", "payload": {"sku": sku, "device": device}}

        async with httpx.AsyncClient() as client:

            response = await client.post(f"{BASE_URL}/router/api/v1/device/state", headers=headers, json=body)

        if response.status_code == 200:
            if "payload" in response.json():
                payload = response.json()["payload"]
                if "capabilities" in payload:
                    return payload["capabilities"]

        else:
            log.warning(f"Failed to get device state: {response.status_code} - {response.text}")
    except Exception as e:
        log.error(f"Failed to get device state: {e}")
        raise e


async def control_device(api_key: str, sku: str, device: str, capability: dict) -> bool:
    headers = {'Govee-API-Key': api_key, 'Content-Type': 'application/json'}
    body = {"requestId": "uuid", "payload": {"sku": sku, "device": device, "capability": capability}}

    async with httpx.AsyncClient() as client:

        response = await client.post(f"{BASE_URL}/router/api/v1/device/control", headers=headers, json=body)

    return response.status_code == 200
