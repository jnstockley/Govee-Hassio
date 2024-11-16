# Govee Home Assistant Integration
This is a custom integration for Home Assistant that allows you to integrate your Govee devices into Home Assistant. 
This integration uses the Govee API to communicate with your devices.

## Setup
1. Install [Hacs](https://hacs.xyz/docs/use/download/download/)
2. Add this repository as a custom repository in Hacs: https://github.com/jnstockley/Govee-Hassio
3. Install the Govee integration from Hacs
4. Add configuration to your `configuration.yaml` file
5. Restart Home Assistant

## Example Configuration
```yaml
# Fan Example
fan:
  - platform: govee
    device_id: <Device ID>
    api_key: <Govee API Key>
    name: <Device SKU>
  - platform: govee
    device_id: <Device ID>
    api_key: <Govee API Key>
    name: <Device SKU>
# Thermometer Example
senor:
  - platform: govee
    device_id: <Device ID>
    api_key: <Govee API Key>
    name: <Device SKU>
 ```

## Get Device ID
1. Make an HTTP GET Request to `https://openapi.api.govee.com/router/api/v1/user/devices`
2. Make sure to include the `Govee-API-Key` header with your Govee API Key
3. The `device` value is your device ID
4. The `sku` is the device SKU, used in the name configuration 

## Supported Devices
- Wi-Fi Thermometer (H5179)
- Wi-Fi Smart Tower Fan (H7102)
- W-Fi Smart Air Purifier (H7126) (WiP)