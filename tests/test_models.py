# SPDX-License-Identifier: GPL-2.0-or-later
from hpeasy.models import Device


def test_device_display_name():
    assert Device("LaserJet 1020", "usb").display_name == "HP LaserJet 1020"
