import logging
from typing import Literal

import httpx

from custom_components.govee.devices.Exceptions import UnauthorizedException, InvalidDeviceException

BASE_URL = "https://openapi.api.govee.com"
BASE_URL_V2 = "https://developer-api.govee.com"
log = logging.getLogger()


async def __get_devices__(api_key) -> dict:
    url = f"{BASE_URL}/router/api/v1/user/devices"
    headers = {"Govee-API-Key": api_key, "Content-Type": "application/json", "Host": "openapi.api.govee.com"}

    response = await __send_request__(url, 'GET', headers=headers)

    data = response['data']

    devices: {str: list[str]} = {}

    for device in data:
        if device['sku'] in devices.keys():
            sku = device['sku']
            devices[sku].append(device['device'])
        else:
            devices[device['sku']] = [device['device']]

    return devices


async def __get_data__(api_key: str, sku: str, device_id: str) -> dict:
    url = f"{BASE_URL}/router/api/v1/device/state"
    headers = {"Govee-API-Key": api_key, "Content-Type": "application/json", "Host": "openapi.api.govee.com"}
    body = {"requestId": "uuid", "payload": {"sku": sku, "device": device_id}}

    return await __send_request__(url, 'POST', headers, body)


async def __control_device__(api_key: str, sku: str, device_id: str, capability: dict, v2_api: bool = False) -> bool:
    if v2_api:
        url = f"{BASE_URL_V2}/v1/appliance/devices/control"
        headers = {"Govee-API-Key": api_key, "Content-Type": "application/json", "Host": "developer-api.govee.com"}
        body = {"model": sku, "cmd": capability, "device": device_id}

        response = await __send_request_v2__(url, headers, body)

        msg: str = response['message']
        code = int(response['code']) if "code" in dict(response).keys() else int(response['status'])

        if msg == "Success" and code == 200:
            return True
        else:
            return False
    else:
        url = f"{BASE_URL}/router/api/v1/device/control"
        headers = {"Govee-API-Key": api_key, "Content-Type": "application/json", "Host": "openapi.api.govee.com"}
        body = {"requestId": "uuid", "payload": {"sku": sku, "device": device_id, "capability": capability}}

        expected_value = capability['value']

        response = await __send_request__(url, 'POST', headers, body)

        msg = response['msg']
        code: int = int(response['code'])
        state: bool = True if response['capability']['state']['status'] == 'success' else False
        value = response['capability']['value']

        if msg == "success" and code == 200 and state and value == expected_value:
            return True
        else:
            log.warning(f"Message: {msg}")
            log.warning(f"Code: {code}")
            log.warning(f"State: {str}")
            log.info(f"Expected Value: {expected_value}, Value: {value}")
            return False


async def __send_request__(url: str, method: Literal['POST', 'GET'], headers: dict = None, body: dict = None) -> dict:
    async with httpx.AsyncClient() as client:
        if method == 'POST':
            response = await client.post(url, json=body, headers=headers)
        elif method == 'GET':
            response = await client.get(url, headers=headers)

    log.info(response.text)

    if response.status_code != 200:
        if response.status_code == 400:
            raise UnauthorizedException("Invalid API Key")
        raise Exception(f"Unknown Error Occurred. Error Code: {response.status_code}, Error Message: {response.text}")

    msg = response.json()['msg'] if 'msg' in response.json().keys() else response.json()['message']

    if msg == "devices not exist":
        payload = response.json()['payload']
        sku = payload['sku']
        device = payload['device']
        raise InvalidDeviceException(f"Device with SKU: {sku} and ID: {device} was not found")

    return response.json()


async def __send_request_v2__(url: str, headers: dict = None, body: dict = None) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.put(url, json=body, headers=headers)

    log.info(response.text)

    code = int(response.json()['code']) if "code" in dict(response.json()).keys() else int(response.json()['status'])

    if response.status_code == 400 or code == 400:
        pass
    elif response.status_code == 401 or code == 401:
        pass
    elif response.status_code == 429 or code == 429:
        pass
    elif response.status_code == 500 or code == 500:
        pass

    return response.json()
