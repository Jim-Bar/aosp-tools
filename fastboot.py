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

from typing import List


class FastbootAdapter(object):
    """
    Provides utility functions for issuing fastboot commands.
    """

    _FASTBOOT = 'fastboot'

    @staticmethod
    def devices() -> List[str]:
        return subprocess.check_output([FastbootAdapter._FASTBOOT, 'devices']).decode().strip().splitlines()

    @staticmethod
    def erase(partition_name: str) -> int:
        return subprocess.check_call([FastbootAdapter._FASTBOOT, 'erase', partition_name])

    @staticmethod
    def flash(partition_name: str, image_path: str) -> int:
        return subprocess.check_call([FastbootAdapter._FASTBOOT, 'flash', partition_name, image_path])

    @staticmethod
    def reboot(bootloader: bool=False) -> int:
        cmd = [FastbootAdapter._FASTBOOT, 'reboot']
        if bootloader:
            cmd.append('bootloader')
        return subprocess.check_call(cmd)

    @staticmethod
    def wipe_userdata() -> int:
        return subprocess.check_call([FastbootAdapter._FASTBOOT, '-w'])
