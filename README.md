# Home Assistant integration for NAD amplifiers, tuners and receivers over serial (RS-232) or Ethernet (telnet)

![Python][python-shield]
[![GitHub Release][releases-shield]][releases]
[![Licence][license-shield]][license]
[![Maintainer][maintainer-shield]][maintainer]
[![Home Assistant][homeassistant-shield]][homeassistant]
[![HACS][hacs-shield]][hacs]  
[![GitHub Sponsors][github-shield]][github]
[![PayPal][paypal-shield]][paypal]
[![BuyMeCoffee][buymecoffee-shield]][buymecoffee]
[![Patreon][patreon-shield]][patreon]

## Introduction

Home Assistant integration to control **[NAD](https://nadelectronics.com/)** amplifiers, tuners and
receivers over serial (RS-232) or Ethernet (telnet).

## Features

- Installation/Configuration through Config Flow UI
- Asynchronous, built on [serialx](https://github.com/puddly/serialx).
- Connects over serial (RS-232) or Ethernet (telnet).
- Supports Serial to Ethernet/WiFi bridge and [ESPHome Serial Proxy](https://esphome.io/components/serial_proxy/)
- Detects the device model and loads the matching configuration.
- Detects the device type for models without configuration.
- Read, set, increment and decrement any supported setting.
- Reads the source names on supported devices.

## Supported protocol

If your device follows the second generation NAD protocol (v2.x), it is supported by this
integration. This protocol is used by NAD amplifiers, tuners and receivers with a serial (RS-232)
or Ethernet port.

The binary protocol that some NAD devices, like the D-series, use on TCP port 50001 is not
supported.

The serial and Ethernet commands are identical. All communication is plain ASCII text. Every
command and response has the format:

`<Prefix>.<Variable><Operator><Value>`

The prefix groups related variables, e.g. `Main`, `Zone2`, `Source1` or `Tuner`. Prefix and
variable together name a setting, e.g. `Main.Volume`. Every message is terminated by a carriage
return and/or line feed.

| Operator | Meaning | Example |
|---|---|---|
| `?` | Query the value | `Main.Volume?` |
| `=` | Set the value | `Main.Volume=-30` |
| `+` | Increment or cycle to the next value | `Main.Volume+` |
| `-` | Decrement or cycle to the previous value | `Main.Volume-` |

The device responds with the `=` operator and the resulting value, e.g. `Main.Volume=-30`.

## Supported devices

The following devices are known to work:

**Receivers:**

- T755
- T757

Additionally, the integrations includes untested configuration files for the following devices:

**Receivers:**

- T765
- T775
- T777
- T785
- T787

**Surround preamplifiers:**

- M15HD
- T175
- T187

**Amplifiers:**

- C356
- C368
- C388

**Tuners:**

- C427

Other NAD devices that use the [supported protocol](#supported-protocol) should work too, with a
basic set of settings: power, model, version, volume, mute and source.

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

- Browse to your Home Assistant instance.
- Go to [**Settings > Devices & services**](https://my.home-assistant.io/redirect/integrations).
- In the bottom right corner, select the [+ Add Integration](https://my.home-assistant.io/redirect/config_flow_start?domain=nad) button.
- From the list, select **NAD**.
- Follow the instructions on screen to complete the setup.

When your wiring is right a new NAD integration and device will now be added to your Integrations
view. If your wiring is not right you will get a *Failed to connect* error message.

## Contribution and appreciation

Do you enjoy using this Home Assistant integration? You can contribute to this integration,
or show your appreciation, in the following ways.

### Contribute your NAD model

Is your NAD device supported by this Home Assistant integration but not listed under Supported
devices? Let me know your NAD model so I can improve the overview of supported devices.
 
### Contribute your language

If you would like to use this Home Assistant integration in your own language you can provide a
translation file as found in the `custom_components/nad/translations` directory. Create a pull
request (preferred) or issue with the file attached.

More on translating custom integrations can be found
[here](https://developers.home-assistant.io/docs/internationalization/custom_integration/).

### Star this integration

Help other Home Assistant and NAD users find this integration by starring this GitHub
page. Click **⭐ Star** on the top right of the GitHub page.

### Support my work

Please consider supporting my work through one of the following platforms, your contribution is
greatly appreciated and keeps me motivated:

[![GitHub Sponsors][github-shield]][github]
[![PayPal][paypal-shield]][paypal]
[![BuyMeCoffee][buymecoffee-shield]][buymecoffee]
[![Patreon][patreon-shield]][patreon]

### Home Assistant support

[Let me answer your Home Assistant questions](https://buymeacoffee.com/rrooggiieerr/e/447353). During
a 1 hour Q&A session I help you solve your Home Assistant related issues.

What can be done in one hour:
- Home Assistant walkthrough, I explain to you what's where in the Home Assistant UI
- Install and configure a Home Assistant integration
- Explain and create scenes
- Explain and create a simple automation
- Install a ZHA quirk, to make your unsupported Zigbee device work in Home Assistant

What takes more time:
- Depending on the severity I might be able to help you with recovering your crashed Home Assistant
- Support for Home Assistant Integration developers

### Hire me

If you would like to have a Home Assistant integration developed for your product or are in need
of a freelance Python developer for your project please contact me, you can find my email address
on [my GitHub profile](https://github.com/rrooggiieerr).

[python-shield]: https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54
[releases]: https://github.com/rrooggiieerr/homeassistant-nad/releases
[releases-shield]: https://img.shields.io/github/v/release/rrooggiieerr/homeassistant-nad?style=for-the-badge
[license]: ./LICENSE
[license-shield]: https://img.shields.io/github/license/rrooggiieerr/homeassistant-nad?style=for-the-badge
[maintainer]: https://github.com/rrooggiieerr
[maintainer-shield]: https://img.shields.io/badge/MAINTAINER-%40rrooggiieerr-41BDF5?style=for-the-badge
[homeassistant]: https://www.home-assistant.io/
[homeassistant-shield]: https://img.shields.io/badge/home%20assistant-%2341BDF5.svg?style=for-the-badge&logo=home-assistant&logoColor=white
[hacs]: https://hacs.xyz/
[hacs-shield]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge
[paypal]: https://paypal.me/seekingtheedge
[paypal-shield]: https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white
[buymecoffee]: https://www.buymeacoffee.com/rrooggiieerr
[buymecoffee-shield]: https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black
[github]: https://github.com/sponsors/rrooggiieerr
[github-shield]: https://img.shields.io/badge/sponsor-30363D?style=for-the-badge&logo=GitHub-Sponsors&logoColor=#EA4AAA
[patreon]: https://www.patreon.com/seekingtheedge/creators
[patreon-shield]: https://img.shields.io/badge/Patreon-F96854?style=for-the-badge&logo=patreon&logoColor=white
