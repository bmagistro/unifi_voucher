# Unifi Voucher

This project is heavily based on work done by the Santa Barbra Hackerspace[1][2][3] and designed to integrate with
the Unifi controller running as a docker container[4].

### Container Python

This script is heavily commented and configured via environment variables.

This script has been processed through `isort`, `black`, `mypy`, and `pylint`.

### Voucher Printer Software

This script is reasonably commented and attemepts to utilize self documenting names. Most configuration is in `config.py`
with some additional items (spacing) still in the script.  Since we know the width, it should be possible to calculate
the spacing and avoid needing to touch the script in the future.

This script has been processed through `isort`, `black`, `mypy`, and `pylint`.

### Voucher Printer Hardware

Similar to the Santa Barbra Hackerspace, the Hillpow 58MM thermal printer was used. While the link to the specific
product looks to be unavailable for purchase, there are a number of similar looking printers available for sale.  The
spacing comments in the code assume a 58MM printer, so if a different size is used, some adjustments may be needed. Some
of the current offerings also include bluetooth (potential comms option to the RPi).

For this build a RPi Zero-W was used and embedded inside of the printer. Additionally the USB port of the printer was
removed and transitioned to headers to allow for a connection the RPi. While this was purpose built and involved
removing the USB port on the PRi, a smarter option would have been to utilize a right angle USB cable. In place of the
printer's USB port a USB to serial adapter was installed to provide a console connection without the need to open the
device up once assemebled. Power is obtained via a regulator to step down the 12V printer is supplied.

For this build GPIO 22 is used for a LED in the button and GPIO 24 is used for the button. You can use any GPIO you
want. The `config.py` file will need to be updated if different GPIOs are used.

### RPi Setup

Initial RPi setup is outside the scope of this document, but there are several guides[5] available online by searching.
It is assumed that your RPi can connect to the internet to install software.

The RPi is running Bullseye now (previously Stretch) so software information assumes Bullseye and may need to be
adjusted. The script is setup to run as a systemd service. An assumption was made that the files would be located in
`/opt/guest_voucher/`. If changed, the `voucher_printer.service` file will need to be updated. This file should be
copied to `/etc/systemd/system/` and `systemctl daemon-reload` called to allow systemd to detect the new service file.
If this file is edited, that will need to be called again to allow systemd to detect the changes.

While best practices are to utilize a virtual environment, we opted to use the system install for two reasons 1) this
is a purpose built device and 2) there are system python modules/packages that are required. Specifically, 
`python3-pil` and `python3-rpi.gpio` are required. Both are architecture specific and easier to install via apt than
pip. While `python3-pil` should include the necessary dependencies, it may be possible that `libopenjp2-7` and `libtiff5`
are also required to be installed. From pip, install `requests` and `python-escpos`. The `python-escpos` module is used
to communicate with the printer. Version 2.2.0 was used initially, but have also confirmed version 3.0 (still alpha)
will also work.

With the dependencies installed, run `mkdir /opt/guest_voucher` and copy the `config.py` and `voucher_printer.py` files
to this directory. Edit `config.py` updating `LOGO_PATH`, `VOUCHER_URL`, `SSID`, and `SSID_PASS` with your values. If
a logo is not included, you will need to edit `voucher_printer.py` and remove the `printer.image(...` line. The
`LOGO_PATH` should be an absolute path. The `VOUCHER_URL` will be along the lines of
`http://<container host>:<exposed port>/voucher/new`. See container script comments for more details/options.

At this point everything should be connected/configured. The RPi should also be able to be rebooted and start this
script.

----

[1] https://hackaday.com/2017/02/10/press-button-get-hackspace-wi-fi-code/

[2] https://sbhackerspace.com/2017/02/08/raspberry-pi-wi-fi-guest-code-generator/

[3] https://gist.github.com/gholms/760fa4f6621c91001b9f2b449e4e4155

[4] https://github.com/jacobalberty/unifi-docker

[5] https://projects.raspberrypi.org/en/projects/raspberry-pi-setting-up
