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

import argparse
import os
import re

from configuration import Configuration


class CommandLineAdapter(object):
    def __init__(self, configuration: Configuration) -> None:
        parser = argparse.ArgumentParser(description='Clone, build and flash an AOSP',
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        # Required arguments.
        required_group = parser.add_argument_group('required arguments')
        required_group.add_argument('-r', '--release',
                                    help='Android release tag (e.g. android-8.1.0_r20)',
                                    required=True,
                                    default=argparse.SUPPRESS)
        required_group.add_argument('-v', '--version',
                                    help='version code of XpertEye (e.g. 4.0.0)',
                                    required=True,
                                    default=argparse.SUPPRESS)

        # Optional arguments.
        parser.add_argument('-d', '--device',
                            help='device code name',
                            choices=configuration.devices(),
                            default=configuration.default_device())
        parser.add_argument('-g', '--generic',
                            help='generic Git ref (e.g. generic-int)',
                            default=configuration.default_generic_ref())
        parser.add_argument('-n', '--name',
                            help='named prefix added to the name of the directory of the AOSP',
                            default=configuration.default_name())
        parser.add_argument('-c', '--cores',
                            help='number of cores to use; 0 for all cores',
                            default=configuration.default_num_cores(),
                            type=int)
        parser.add_argument('-w', '--path',
                            help='path to the AOSP',
                            default=configuration.default_path())
        parser.add_argument('-p', '--project',
                            help='project of XpertEye',
                            choices=configuration.projects(),
                            default=configuration.default_project())
        parser.add_argument('-x', '--variant',
                            help='build variant',
                            choices=configuration.profiles(),
                            default=configuration.default_profile())
        parser.add_argument('-s', '--specific',
                            help='specific Git ref (e.g. sailfish-8.1.0-int)',
                            default=configuration.default_specific_ref())

        # Constant arguments.
        parser.add_argument('-b', '--build',
                            help='build the AOSP',
                            action='store_true')
        parser.add_argument('-o', '--ota',
                            help='build the OTA package',
                            action='store_true')
        parser.add_argument('-u', '--update',
                            help='build the update package',
                            action='store_true')

        # Parse and sanity checks.
        self._args = parser.parse_args()
        if self.num_cores() and not self.build() and not self.ota_package() and not self.update_package():
            parser.error('-c/--cores requires -b/--build or -o/--ota or -u/--update')
        android_release_tags = {tag for tag in configuration.repository_build().remote_refs()[1]
                                if bool(re.match('^android-\d\.\d\.\d_r\d\d$', tag))}
        if not os.path.exists(self.path()):
            parser.error('Path {} does not exist'.format(self.path()))
        if os.path.exists(os.path.join(self.path(), self.name())):
            parser.error('Path {} already exists'.format(self.path()))
        if self.release() not in android_release_tags:
            parser.error('Android release {} does not exist'.format(self.release()))
        heads, tags = configuration.repository_local_manifest().remote_refs()
        if self.specific_ref() not in heads and self.specific_ref() not in tags:
            parser.error('Specific Git reference {} does not exist'.format(self.specific_ref()))

    def build(self) -> bool:
        return self._args.build

    def device(self) -> str:
        return self._args.device

    def generic_ref(self) -> str:
        return self._args.generic

    def name(self) -> str:
        return self._args.name

    def num_cores(self) -> int:
        return self._args.cores

    def ota_package(self) -> bool:
        return self._args.ota

    def path(self) -> str:
        return os.path.realpath(self._args.path)

    def project(self) -> str:
        return self._args.project

    def variant(self) -> str:
        return self._args.variant

    def release(self) -> str:
        return self._args.release

    def specific_ref(self) -> str:
        return self._args.specific

    def update_package(self) -> bool:
        return self._args.update

    def version(self) -> str:
        return self._args.version
