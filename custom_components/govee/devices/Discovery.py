from custom_components.govee.const import SUPPORTED_DEVICES
from custom_components.govee.devices import Generic


async def get_devices():
    devices = await Generic.__get_devices__('d8c587b9-c919-42d5-b7eb-324f2186c81d')

    supported_devices: {str: list[str]} = {}

    for device in devices:

        if device in SUPPORTED_DEVICES:
            supported_devices[device] = devices[device]

    return devices, supported_devices


print(get_devices())
