# TODO: hashbang to virtualenv.
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

from commandline import CommandLineAdapter
from configuration import Configuration


class AOSP(object):
    """
    Clone, build and flash an Android Open Source Project.
    """


class AOSPEnvironment(object):
    """
    All the characteristics of an Android Open Source Project.
    """

    def __init__(self, path: str, prefix: str, release: str, profile: str, device: str,
                 specific_ref: str, generic_ref: str, version: str, project: str) -> None:
        self._path = os.path.realpath(path)
        self._name = '{}_{}_{}_{}'.format(prefix, release, profile, device)
        self._release = release
        self._profile = profile
        self._device = device
        self._specific_ref = specific_ref
        self._generic_ref = generic_ref
        self._version = version
        self._project = project

    def __str__(self) -> str:
        description = ''
        description += 'Path: {}\n'.format(self._path)
        description += 'Name: {}\n'.format(self._name)
        description += 'Release: {}\n'.format(self._release)
        description += 'Profile: {}\n'.format(self._profile)
        description += 'Device: {}\n'.format(self._device)
        description += 'Version: {}\n'.format(self._version)
        description += 'Project: {}\n'.format(self._project)
        description += 'Generic ref: {}\n'.format(self._generic_ref)
        description += 'Specific ref: {}'.format(self._specific_ref)

        return description


def main():
    cli = CommandLineAdapter(Configuration.read_configuration())
    environment = AOSPEnvironment(cli.path(), cli.name(), cli.release(), cli.profile(), cli.device(),
                                  cli.specific_ref(), cli.generic_ref(), cli.version(), cli.project())
    print(environment)


if __name__ == '__main__':
    main()
