import requests

BASE_URL = "https://openapi.api.govee.com"


def get_device_state(api_key: str, sku: str, device: str):
    headers = {'Govee-API-Key': api_key, 'Content-Type': 'application/json'}
    body = {"requestId": "uuid", "payload": {"sku": sku, "device": device}}

    response = requests.post(f"{BASE_URL}/router/api/v1/device/state", headers=headers, json=body)

    if response.status_code == 200:
        if "payload" in response.json():
            payload = response.json()["payload"]
            if "capabilities" in payload:
                return payload["capabilities"]


def control_device(api_key: str, sku: str, device: str, capability: dict) -> bool:
    headers = {'Govee-API-Key': api_key, 'Content-Type': 'application/json'}
    body = {"requestId": "uuid", "payload": {"sku": sku, "device": device, "capability": capability}}

    response = requests.post(f"{BASE_URL}/router/api/v1/device/control", headers=headers, json=body)

    return response.status_code == 200
