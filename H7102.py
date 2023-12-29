# GoveeLife 36'' Smart Tower Fan
# https://www.goveelife.com/products/goveelife-smart-home-appliances-H7102
import Generic
# from . import log


class H7102:
    def __init__(self, data: dict):
        payload: dict = data['payload']
        capabilities: dict = payload['capabilities']
        self.sku = payload['sku']
        self.device = payload['device']
        for capability in capabilities:
            if capability['type'] == 'devices.capabilities.online':
                self.online: bool = bool(capability['state']['value'])
            elif capability['type'] == 'devices.capabilities.on_off':
                self.on: bool = bool(int(capability['state']['value']))
            elif capability['type'] == 'devices.capabilities.toggle':
                self.oscillation: bool = bool(capability['state']['value'])
            elif capability['type'] == 'devices.capabilities.work_mode':
                self.work_mode: dict[str: int] = {'mode': capability['state']['value']['workMode'],
                                                  'value': capability['state']['value']['modeValue']}
            #else:
            #    log.warning(f'Unexpected capability found {capability['type']}')

    def __str__(self):
        return (f'SKU: {self.sku}, Device: {self.device}, Online: {self.online}, On: {self.on}, '
                f'Oscillation: {self.oscillation}, Work Mode: {self.work_mode}')


BASE_URL = "https://openapi.api.govee.com"


def get_data(api_key: str, mac_address: str) -> H7102:
    data = Generic.__get_data__(api_key, "H7102", mac_address)

    device: H7102 = H7102(data)

    return device


def on_off(api_key: str, mac_address: str, on: bool) -> bool:
    capability = {"type": "devices.capabilities.on_off", "instance": "powerSwitch", "value": int(on)}

    return Generic.__control_device__(api_key, "H7102", mac_address, capability)


def toggle_oscillation(api_key: str, mac_address: str, oscillation: bool) -> bool:
    capability = {"type": "devices.capabilities.toggle", "instance": "oscillationToggle", "value": int(oscillation)}

    return Generic.__control_device__(api_key, "H7102", mac_address, capability)


def change_mode_speed(api_key: str, mac_address: str, mode: int = 0, value: int = 0) -> bool:
    device = get_data(api_key, mac_address)

    mode_enum = {2: "custom", 3: "auto", 5: "sleep", 6: "nature"}

    responses = []

    if mode != 0 and mode in mode_enum.keys():
        capability = {"name": "mode", "value": mode}
        responses.append(Generic.__control_device__(api_key, "H7102", mac_address, capability, v2_api=True))

    if value in range(1, 9):
        capability = {"name": "gear", "value": value}
        responses.append(Generic.__control_device__(api_key, "H7102", mac_address, capability, v2_api=True))

    # responses.append(on_off(api_key, mac_address, device.on))

    return all(responses)


device = get_data(api_key='d8c587b9-c919-42d5-b7eb-324f2186c81d', mac_address='18:43:D4:AD:FC:BB:44:DA')

on_off(api_key='d8c587b9-c919-42d5-b7eb-324f2186c81d', mac_address='18:43:D4:AD:FC:BB:44:DA', on=True)
