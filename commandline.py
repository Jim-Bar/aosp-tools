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
        parser = argparse.ArgumentParser(description='Clone, build and flash an AOSP')

        # Required arguments.
        required_group = parser.add_argument_group('required arguments')
        required_group.add_argument('-r', '--release',
                                    help='Android release tag (e.g. android-8.1.0_r20)',
                                    required=True)
        required_group.add_argument('-v', '--version',
                                    help='version code (e.g. 4.0.0)',
                                    required=True)

        # Optional arguments.
        parser.add_argument('-d', '--device',
                            help='device name',
                            choices=configuration.devices(),
                            default=configuration.default_device())
        parser.add_argument('-g', '--generic',
                            help='generic Git ref (e.g. generic-int)',
                            default=configuration.default_generic_ref())
        parser.add_argument('-n', '--name',
                            help='named prefix added to the name of the directory of the AOSP',
                            default=configuration.default_name())
        parser.add_argument('-w', '--path',
                            help='path to the AOSP',
                            default=configuration.default_path())
        parser.add_argument('-p', '--project',
                            help='project',
                            choices=configuration.projects(),
                            default=configuration.default_project())
        parser.add_argument('-u', '--profile',
                            help='build profile',
                            choices=configuration.profiles(),
                            default=configuration.default_profile())
        parser.add_argument('-s', '--specific',
                            help='specific Git ref (e.g. sailfish-8.1.0-int',
                            default=configuration.default_specific_ref())

        # Parse and sanity checks.
        self._args = parser.parse_args()
        android_release_tags = {tag for tag in configuration.repository_build().remote_refs()[1]
                                if bool(re.match('^android-\d\.\d\.\d_r\d\d$', tag))}
        assert os.path.exists(self.path())
        assert self.release() in android_release_tags
        heads, tags = configuration.repository_local_manifest().remote_refs()
        assert self.specific_ref() in heads or self.specific_ref() in tags

    def device(self) -> str:
        return self._args.device

    def generic_ref(self) -> str:
        return self._args.generic

    def name(self) -> str:
        return self._args.name

    def path(self) -> str:
        return os.path.realpath(self._args.path)

    def project(self) -> str:
        return self._args.project

    def profile(self) -> str:
        return self._args.profile

    def release(self) -> str:
        return self._args.release

    def specific_ref(self) -> str:
        return self._args.specific

    def version(self) -> str:
        return self._args.version
