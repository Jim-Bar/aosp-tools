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

import os
import sys

from adb import ADBAdapter
from commandline import FlasherCommandLineInterface
from configuration import Configuration
from fastboot import FastbootAdapter
from sanity import SanityChecks


class Flasher(object):
    @staticmethod
    def flash(system_image_path: str, vbmeta_image_path: str) -> None:
        if ADBAdapter.devices():
            ADBAdapter.reboot('bootloader')
        FastbootAdapter.erase('system')
        FastbootAdapter.erase('vbmeta')
        FastbootAdapter.wipe_userdata()
        FastbootAdapter.flash('system', system_image_path)
        FastbootAdapter.flash('vbmeta', vbmeta_image_path)
        FastbootAdapter.reboot()

    @staticmethod
    def description(system_image_path: str, vbmeta_image_path: str) -> str:
        description = list()
        description.append('Notes:')
        description.append('- the device must be unlocked')
        description.append('- the partitions listed below will be erased (make sure you can restore them)')
        description.append('- the user data will be wiped')
        description.append('- the device will not be relocked automatically once flashed')
        description.append('Will flash:')
        description.append('- "{}" on partition "system"'.format(system_image_path))
        description.append('- "{}" on partition "vbmeta"'.format(vbmeta_image_path))
        description.append('=' * max(map(len, description)))
        description.insert(0, description[-1])

        return '\n'.join(description)


def main() -> None:
    SanityChecks.run()

    cli = FlasherCommandLineInterface(Configuration.read_configuration())
    print(Flasher.description(cli.system_image_path(), cli.vbmeta_image_path()))
    if cli.press_enter():
        Flasher.flash(cli.system_image_path(), cli.vbmeta_image_path())
    else:
        sys.exit(os.EX_USAGE)  # Set an error code for canceling chained commands.


if __name__ == '__main__':
    main()
