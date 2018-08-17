#!/usr/bin/env python3
# -*- coding:utf8  -*-

#
# MIT License
#
# Copyright (c) 2018-2021 Jean-Marie BARAN (jeanmarie.baran@gmail.com)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import subprocess
import time

from typing import List


class ADBAdapter(object):
    """
    Provides utility functions for issuing ADB commands.
    """

    _ADB = 'adb'

    @staticmethod
    def devices() -> List[str]:
        return subprocess.check_output([ADBAdapter._ADB, 'devices']).decode().strip().splitlines()[1:]

    @staticmethod
    def pull(*files) -> int:
        return subprocess.check_call([ADBAdapter._ADB, 'pull'] + list(files))

    @staticmethod
    def push(*files) -> int:
        return subprocess.check_call([ADBAdapter._ADB, 'push'] + list(files))

    @staticmethod
    def reboot(option: str='') -> int:
        reboot_options = ['bootloader', 'recovery', 'sideload', 'sideload-auto-reboot']
        if option and option not in reboot_options:
            raise ValueError('Invalid reboot option: {}'.format(option))
        return subprocess.check_call([ADBAdapter._ADB, 'reboot', option])

    @staticmethod
    def shell(*args) -> str:
        return subprocess.check_output([ADBAdapter._ADB, 'shell'] + list(args)).decode().strip()

    @staticmethod
    def wait_for_boot_completed() -> None:
        ADBAdapter.wait_for_device()
        while ADBAdapter.shell('getprop', 'sys.boot_completed') != '1':
            time.sleep(1)

    @staticmethod
    def wait_for_device() -> int:
        return subprocess.check_call([ADBAdapter._ADB, 'wait-for-device'])

    @staticmethod
    def wait_for_shutdown() -> None:
        ADBAdapter.shell()
