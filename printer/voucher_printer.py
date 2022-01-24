"""
SPDX-License-Identifier: GPL-3.0-or-later

Application to communicate with Unifi Voucher Controller for printing guest wireless access tickets
"""

import datetime
import signal
import time
import typing

import requests
import escpos.printer  # type: ignore
import RPi.GPIO  # type: ignore

# App config file
# pylint: disable-next=wildcard-import
from config import *

# pylint: disable-next=invalid-name
running: bool = True


def cb_print_code(channel: int) -> None:
    """
    GPIO event call back
    When the button is pressed this is what is ran
    Drop LED to indicate processing, make request, print, restore LED
    """
    del channel
    print("Guest access ticket requested")

    RPi.GPIO.output(GPIO_LED, RPi.GPIO.HIGH)

    req = requests.post(VOUCHER_URL, json={})
    if req.status_code != requests.codes.ok:
        print(f"Failed to obtain voucher code, {req.status_code}")
    else:
        resp = req.json()
        created = datetime.datetime.fromtimestamp(resp["create_time"], datetime.timezone.utc)
        print("Successfully obtained voucher code")
        # char width = 32
        printer = escpos.printer.File(DEV_LPR)
        printer.set(align="center")
        printer.image(LOGO_PATH, impl="bitImageColumn")
        printer.text("\n")
        printer.text(created.strftime("%Y-%m-%d %H:%M %Z") + "\n\n")
        printer.set(align="left")
        printer.text("SSID:                     ")
        printer.set(height=2)
        printer.text(f"{SSID}\n")
        printer.set(height=1)
        printer.text("Password:         ")
        printer.set(height=2)
        printer.text(f"{SSID_PASS}\n")
        printer.set(height=1)
        printer.text("Code:                ")
        printer.set(height=2)
        printer.text(f"{resp['code'][:5]}-{resp['code'][5:]}\n")
        printer.set(align="center", height=1)
        printer.text("\nValid for 8 hours\n")
        printer.text("\n\n\n")
        printer.flush()
        printer.close()

    time.sleep(1)
    RPi.GPIO.output(GPIO_LED, RPi.GPIO.LOW)


# the actual type def is a bit more complicated...
# mypy expects: typing.Union[typing.Callable[[int, typing.Optional[??.FrameType]], typing.Any], int, signal.Handlers, None]
def sigint_handler(sig: int, frame: typing.Any) -> None:
    """
    Application termination signal handler
    """
    del sig
    del frame
    # pylint: disable-next=global-statement,invalid-name
    global running
    running = False


def main() -> None:
    """
    Main appliaction loop
    This handles gpio configuration, gpio event detection, and app signal handling
    """
    signal.signal(signal.SIGINT, sigint_handler)

    RPi.GPIO.setmode(RPi.GPIO.BCM)

    RPi.GPIO.setup(GPIO_LED, RPi.GPIO.OUT)
    RPi.GPIO.output(GPIO_LED, RPi.GPIO.LOW)

    RPi.GPIO.setup(GPIO_BTN, RPi.GPIO.IN, pull_up_down=RPi.GPIO.PUD_OFF)
    RPi.GPIO.add_event_detect(GPIO_BTN, RPi.GPIO.FALLING, callback=cb_print_code, bouncetime=BTN_BOUNCE_MS)

    while running:
        time.sleep(0.5)

    RPi.GPIO.output(GPIO_LED, RPi.GPIO.HIGH)


if __name__ == "__main__":
    main()
