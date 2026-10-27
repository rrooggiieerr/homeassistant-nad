# Home Assistant integration for NAD amplifiers, tuners and receivers over serial (RS-232) or Ethernet (telnet)

![Python][python-shield]
[![GitHub Release][releases-shield]][releases]
[![Licence][license-shield]][license]
[![Maintainer][maintainer-shield]][maintainer]
[![Home Assistant][homeassistant-shield]][homeassistant]
[![HACS][hacs-shield]][hacs]  
[![GitHub Sponsors][github-shield]][github]
[![BuyMeCoffee][buymecoffee-shield]][buymecoffee]

## Introduction

Home Assistant integration to control **[NAD](https://nadelectronics.com/)** amplifiers, tuners and
receivers over serial (RS-232) or Ethernet (telnet).

⚠️ This custom integration replaces the NAD integration that comes with Home Assistant Core. If your
NAD device does not follow the v2.x NAD protocol this integration will not work.

## Features

- Installation/Configuration through Config Flow UI.
- Discovers devices on the network through DHCP and Zeroconf (experimental).
- Imports YAML configuration as used by Home Assistant Core.
- Asynchronous, built on [serialx](https://github.com/puddly/serialx).
- Connects over serial (RS-232) or Ethernet (telnet).
- Supports Serial to Ethernet/WiFi bridge and [ESPHome Serial Proxy](https://esphome.io/components/serial_proxy/).
- Detects the device model and build and loads the matching configuration.
- Detects the device type (amplifier, tuner, receiver) for models without configuration.
- Read, set, increment and decrement any supported setting.
- Reads the source names on supported devices.
- Supports zones on multi-zone amplifiers and receivers.
- Reconfigure the serial port or URL without removing the device.
- Send any command to the device with the *Send command* action.
- Send IR codes to the device with the *Send IR code* action.

## Supported protocol

If your device follows the second generation NAD protocol (v2.x), it is supported by this
integration. This protocol is used by NAD amplifiers, tuners and receivers with a serial (RS-232)
or Ethernet port.

⚠️ The binary protocol that some NAD devices, like the D-series, use on TCP port 50001 is not
supported.

Commands for the second generation NAD protocol have the following format:

`<Setting><Operator><Value>` like `Main.Volume=-30`

[Read more about the supported protocol.](https://github.com/rrooggiieerr/nad_serial.py#supported-protocol)

## Supported devices

The following devices are known to work:

**Receivers:**

- T755
- T757

Additionally, the integration includes untested configuration files for the following devices:

**Receivers:**

- T175
- T187
- T758
- T765
- T775
- T777
- T778
- T785
- T787

**Surround preamplifiers:**

- M15HD
- M17
- M51
- T175
- T187

**Amplifiers:**

- C328
- C338
- C356
- C368
- C388

**Tuners:**

- C427

Other NAD devices that use the [supported protocol](https://github.com/rrooggiieerr/nad_serial.py#supported-protocol)
should work too, with a basic set of settings: power, model, version, volume, mute and source.

## Connecting

### USB to serial adapter

If your device has a serial port, use a USB to serial adapter to connect it. See the documentation
of your device for the location of the serial port and how to wire it.

### Ethernet

If your device has an Ethernet port use a network cable to connect your device to a router.

Use `socket://<ip address>:23` as the URL if the device is not automatically discovered.

### Serial to Ethernet/WiFi bridge

A serial to Ethernet/WiFi bridge is useful when the device is not close to your Home Assistant
server. Configure the bridge for 115200 baud, 8N1.

Use `socket://<ip address>:<port>` or `rfc2217://<ip address>:<port>` as the URL, depending on
which protocol the bridge supports.

### ESPHome Serial Proxy

Build your own ESPHome Serial Proxy using an ESP32 and a serial to TTL converter. Install [ESPHome Serial Proxy](https://esphome.io/components/serial_proxy/)
and select the Serial Proxy in the configuration flow.

Example Serial Proxy using a Wemos C3 Mini:

<img src="https://raw.githubusercontent.com/rrooggiieerr/homeassistant-nad/main/serial_proxy.png" style="width: 25%;"/>

⚠️ Unlike this image you need a male connector on the serial to TTL converter

## Installation

### HACS

The recommended way to install this Home Assistant integration is by using [HACS][hacs].
Click the following button to open the integration directly on the HACS integration page.

[![Install NAD from HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=rrooggiieerr&repository=homeassistant-nad&category=integration)

### Manually

- Copy the `custom_components/nad` directory of this repository into the
`config/custom_components/` directory of your Home Assistant installation
- Restart Home Assistant

## Adding a new NAD device

### YAML import

Existing YAML configurations as used by the Home Assistant Core NAD integration are imported
automatically.

`min_volume`, `max_volume`, `volume_step` and `sources` are no longer used; the integration takes
them from the device or device configuration. TCP type YAML configurations are not supported;
uninstall this custom integration and keep using the Home Assistant Core NAD integration for these
devices.

After a successful import you can remove the YAML configuration.

### Discovery

NAD devices with an Ethernet port are discovered automatically on your network. Go to
[**Settings > Devices & services**](https://my.home-assistant.io/redirect/integrations) and select
**Add** on the discovered NAD device.

### Manually

- Browse to your Home Assistant instance.
- Go to [**Settings > Devices & services**](https://my.home-assistant.io/redirect/integrations).
- In the bottom right corner, select the [+ Add Integration](https://my.home-assistant.io/redirect/config_flow_start?domain=nad) button.
- From the list, select **NAD**.
- Select the serial port or provide the URL.

ⓘ To connect to the Ethernet (telnet) interface of your device use `socket://<ip address>:23`

When your connection is right a new NAD integration and device will now be added to your Integrations
view. If your connection is not right you will get a *Failed to connect* error message.

## Actions

### Send command

The `nad.send_command` action sends any command to the device and returns the response. Use it for
settings that have no entity.

| Field     | Description                                                   |
|-----------|---------------------------------------------------------------|
| Device    | The NAD device to send the command to.                        |
| Setting   | The setting, like `Main.Volume`.                              |
| Operator  | `?` to query, `=` to set, `+` to increment, `-` to decrement. |
| Value     | The value, only used with the `=` operator.                   |

```yaml
action: nad.send_command
data:
  config_entry_id: <your NAD device>
  setting: Main.Volume
  operator: "?"
response_variable: result
# result.response is -30
```

For settings in the device configuration, the response is converted, for example a boolean setting
returns `true` or `false` instead of `On` or `Off`.

### Send IR code

The `nad.send_ir` action sends an IR code to the device or one of its zones through the serial or
network connection, as if it came from a remote control. It is only available on devices that
support sending IR codes. The device doesn't respond to IR codes, so the action doesn't confirm
that the code was handled.

| Field   | Description                                                                         |
|---------|-------------------------------------------------------------------------------------|
| Device  | The NAD device or zone to send the IR code to.                                      |
| Code    | The IR code to send, in decimal (0-255).                                            |
| Channel | Optional. Channel 0 uses customer code 0x877C, channel 1 uses customer code 0x860F. |

```yaml
action: nad.send_ir
data:
  device_id: <your NAD device or zone>
  code: 148
  channel: 0
```

## Contributing and supporting this project

Are you enjoying this Home Assistant integration? There are several ways you can contribute to the
project, help other users, or support my work.

### Contribute your NAD model

Is your NAD device supported by this Home Assistant integration but not yet listed under
[Supported devices](#supported-devices)? Let me know which NAD model you have so I can improve the
overview of supported devices.

Is your NAD model not fully supported yet? You can help by creating a [configuration file](https://github.com/rrooggiieerr/nad_serial.py/blob/main/nad_serial/configs/README.md)
for your device and submitting it in a pull request.

### Contribute a translation

Would you like to use this integration in your own language? You can help by adding a translation file
to the `custom_components/nad/translations` directory and submitting it in a pull request.

More information about translating Home Assistant custom integrations can be found
[here](https://contributors.home-assistant.io/core/integrations/translations/).

### Star this integration

Help other Home Assistant and NAD users discover this integration by starring the GitHub
repository. Just click **⭐ Star** at the top right of [this page](https://github.com/rrooggiieerr/homeassistant-nad).

### Support my work

I’ve put a lot of time and effort into developing and maintaining this integration. If you find it
useful, please consider supporting its continued development by [sponsoring me on GitHub][github]
or [buying me a coffee ☕️][buymecoffee].

Your support is greatly appreciated and helps keep me motivated to continue developing and
maintaining this integration!

[![GitHub Sponsors][github-shield]][github]
[![BuyMeCoffee][buymecoffee-shield]][buymecoffee]

### Home Assistant support

Need some hands-on help with Home Assistant? [Book a one-hour Q&A session](https://buymeacoffee.com/rrooggiieerr/e/447353)
and I'll help you solve your Home Assistant-related questions.

Examples of what we can cover in one hour:
- Home Assistant walkthrough, I'll explain where to find things in the Home Assistant UI
- Installing and configuring a Home Assistant integration
- Explaining and creating scenes
- Explaining and creating a simple automation
- Install a ZHA quirk to make an unsupported Zigbee device work with Home Assistant

For more complex issues, such as recovering a crashed Home Assistant installation or providing
support for Home Assistant integration developers, I may be able to help as well. These requests
can require more than one hour and may need to be arranged separately.

### Hire me

Would you like a Home Assistant integration developed for your product, or do you need an
experienced Python developer for your project?

I'm available for freelance development work. You can find my contact details on
[my GitHub profile](https://github.com/rrooggiieerr).

[python-shield]: https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54
[releases]: https://github.com/rrooggiieerr/homeassistant-nad/releases
[releases-shield]: https://img.shields.io/github/v/release/rrooggiieerr/homeassistant-nad?style=for-the-badge
[license]: ./LICENSE.md
[license-shield]: https://img.shields.io/github/license/rrooggiieerr/homeassistant-nad?style=for-the-badge
[maintainer]: https://github.com/rrooggiieerr
[maintainer-shield]: https://img.shields.io/badge/MAINTAINER-%40rrooggiieerr-41BDF5?style=for-the-badge
[homeassistant]: https://www.home-assistant.io/
[homeassistant-shield]: https://img.shields.io/badge/home%20assistant-%2341BDF5.svg?style=for-the-badge&logo=home-assistant&logoColor=white
[hacs]: https://hacs.xyz/
[hacs-shield]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge
[buymecoffee]: https://www.buymeacoffee.com/rrooggiieerr
[buymecoffee-shield]: https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black
[github]: https://github.com/sponsors/rrooggiieerr
[github-shield]: https://img.shields.io/badge/sponsor-30363D?style=for-the-badge&logo=GitHub-Sponsors&logoColor=%23EA4AAA
