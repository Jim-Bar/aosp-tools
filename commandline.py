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

import argparse
import os
import re
import sys

from configuration import Configuration


class CommandLineInterface(object):
    def press_enter(self) -> bool:
        if not self._continue_when_prompted():
            try:
                input('Press enter to continue...')
            except KeyboardInterrupt:
                print('')
                return False
        return True

    def _continue_when_prompted(self) -> bool:
        raise NotImplemented


class AOSPBuildCommandLineInterface(CommandLineInterface):
    def __init__(self, configuration: Configuration) -> None:
        parser = argparse.ArgumentParser(description='Build an AOSP tree',
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        # Optional arguments.
        parser.add_argument('-c', '--cores',
                            help='number of cores to use; 0 for all cores',
                            default=configuration.default_num_cores(),
                            type=int)
        parser.add_argument('-w', '--path',
                            help='path to the AOSP tree',
                            default=configuration.default_path())
        parser.add_argument('-t', '--target',
                            help='makefile target to build',
                            default=configuration.default_make_target())
        parser.add_argument('-y', '--yes',
                            help='automatically continue when prompted',
                            action='store_true')

        # Parse and sanity checks.
        self._args = parser.parse_args()
        if self.num_cores() < 0:
            parser.error('-c/--cores must be greater than or equal to zero')
        if not os.path.exists(self.path()):
            parser.error('Path "{}" does not exist'.format(self.path()))

    def make_target(self) -> str:
        return self._args.target

    def num_cores(self) -> int:
        if self._args.cores == 0:  # Resolve the real number of available cores.
            return os.cpu_count()
        return self._args.cores

    def path(self) -> str:
        return os.path.realpath(self._args.path)

    def _continue_when_prompted(self) -> bool:
        return self._args.yes


class AOSPSpecCommandLineInterface(CommandLineInterface):
    def __init__(self, configuration: Configuration) -> None:
        parser = argparse.ArgumentParser(description='Setup the specifications of an AOSP tree',
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        parser.add_argument('-w', '--path',
                            help='path to the AOSP tree',
                            default=configuration.default_path())
        parser.add_argument('-p', '--product',
                            help='name of the target product',
                            default=configuration.default_product())
        parser.add_argument('-u', '--variant',
                            help='build variant',
                            choices=configuration.variants(),
                            default=configuration.default_variant())
        parser.add_argument('-y', '--yes',
                            help='automatically continue when prompted',
                            action='store_true')

        # Parse and sanity checks.
        self._args = parser.parse_args()
        if not os.path.exists(self.path()):
            parser.error('Path "{}" does not exist'.format(self.path()))

    def path(self) -> str:
        return os.path.realpath(self._args.path)

    def product(self) -> str:
        return self._args.product

    def variant(self) -> str:
        return self._args.variant

    def _continue_when_prompted(self) -> bool:
        return self._args.yes


class AOSPTreeCommandLineInterface(CommandLineInterface):
    def __init__(self, configuration: Configuration) -> None:
        parser = argparse.ArgumentParser(description='Clone an AOSP tree. Read a local manifest from standard input',
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        # Required arguments.
        required_group = parser.add_argument_group('required arguments')
        required_group.add_argument('-r', '--release',
                                    help='Android release tag (e.g. android-8.1.0_r41)',
                                    required=True,
                                    default=argparse.SUPPRESS)

        # Optional arguments.
        parser.add_argument('-c', '--cores',
                            help='number of cores to use; 0 for all cores',
                            default=configuration.default_num_cores(),
                            type=int)
        parser.add_argument('-n', '--name',
                            help='name of the directory of the AOSP tree',
                            default=configuration.default_name())
        parser.add_argument('-w', '--path',
                            help='path to the AOSP tree',
                            default=configuration.default_path())
        parser.add_argument('-p', '--prefix',
                            help='prefix added to the name of the directory of the AOSP tree (will copy -r/--release if'
                                 ' not provided)',
                            default=argparse.SUPPRESS)
        parser.add_argument('-y', '--yes',
                            help='automatically continue when prompted',
                            action='store_true')

        # Parse and sanity checks.
        self._args = parser.parse_args()
        if self.num_cores() < 0:
            parser.error('-c/--cores must be greater than or equal to zero')
        if not os.path.exists(os.path.dirname(self.path())):
            parser.error('Path "{}" does not exist'.format(self.path()))
        if os.path.exists(self.path()):
            parser.error('Path "{}" already exists'.format(self.path()))
        android_release_tags = {tag for tag in configuration.repository_build().remote_refs()[1]
                                if bool(re.match('^android-\d\.\d\.\d_r\d\d$', tag))}
        if self.release() not in android_release_tags:
            parser.error('Android release "{}" does not exist'.format(self.release()))
        self._local_manifest_string = sys.stdin.read()
        sys.stdin = open('/dev/tty', 'r')  # "Reopen" standard input. Required for reading further inputs (key presses).

    def local_manifest(self) -> str:
        return self._local_manifest_string

    def num_cores(self) -> int:
        if self._args.cores == 0:  # Resolve the real number of available cores.
            return os.cpu_count()
        return self._args.cores

    def path(self) -> str:
        try:
            prefix = self._args.prefix
        except AttributeError:
            prefix = self.release()
        return os.path.join(os.path.realpath(self._args.path), '{}_{}'.format(prefix, self._args.name))

    def release(self) -> str:
        return self._args.release

    def _continue_when_prompted(self) -> bool:
        return self._args.yes


class FlasherCommandLineInterface(CommandLineInterface):
    def __init__(self, configuration: Configuration) -> None:
        parser = argparse.ArgumentParser(description='Flash a generic system image',
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        # Optional arguments.
        parser.add_argument('-s', '--system',
                            help='path to the system image',
                            default=configuration.default_flash_system_path())
        parser.add_argument('-v', '--vbmeta',
                            help='path to the vbmeta image',
                            default=configuration.default_flash_vbmeta_path())
        parser.add_argument('-y', '--yes',
                            help='automatically continue when prompted',
                            action='store_true')

        # Parse and sanity checks.
        self._args = parser.parse_args()
        if not os.path.exists(self.system_image_path()):
            parser.error('Path "{}" does not exist'.format(self.system_image_path()))
        if not os.path.exists(self.vbmeta_image_path()):
            parser.error('Path "{}" does not exist'.format(self.vbmeta_image_path()))

    def system_image_path(self) -> str:
        return os.path.realpath(self._args.system)

    def vbmeta_image_path(self) -> str:
        return os.path.realpath(self._args.vbmeta)

    def _continue_when_prompted(self) -> bool:
        return self._args.yes


class LocalManifestCommandLineInterface(CommandLineInterface):
    def __init__(self, configuration: Configuration) -> None:
        parser = argparse.ArgumentParser(description='Fetch a local manifest',
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        # Optional arguments.
        parser.add_argument('-g', '--generic',
                            help='generic Git ref',
                            default=configuration.default_generic_ref())
        parser.add_argument('-r', '--revision',
                            help='local manifest Git ref (will copy -s/--specific if not provided)',
                            default=argparse.SUPPRESS)
        parser.add_argument('-s', '--specific',
                            help='specific Git ref',
                            default=configuration.default_specific_ref())

        # Parse and sanity checks.
        self._args = parser.parse_args()
        heads, tags = configuration.repository_local_manifest().remote_refs()
        if self.specific_ref() not in heads and self.specific_ref() not in tags:
            parser.error('Specific Git reference "{}" does not exist'.format(self.specific_ref()))

    def generic_ref(self) -> str:
        return self._args.generic

    def ref(self) -> str:
        try:
            return self._args.ref
        except AttributeError:
            return self.specific_ref()

    def specific_ref(self) -> str:
        return self._args.specific


class SignerCommandLineInterface(CommandLineInterface):
    def __init__(self, configuration: Configuration) -> None:
        parser = argparse.ArgumentParser(description='Sign a target file and generate image and OTA files',
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        # Required arguments.
        required_group = parser.add_argument_group('required arguments')
        required_group.add_argument('-k', '--key',
                                    help='path to the key to use for signing',
                                    required=True,
                                    default=argparse.SUPPRESS)

        # Optional arguments.
        parser.add_argument('-w', '--path',
                            help='path to the AOSP tree',
                            default=configuration.default_path())

        # Parse and sanity checks.
        self._args = parser.parse_args()
        if not os.path.exists(self.key_path()):
            parser.error('Path "{}" does not exist'.format(self.key_path()))
        if not os.path.exists(self.path()):
            parser.error('Path "{}" does not exist'.format(self.path()))

    def key_path(self) -> str:
        return os.path.realpath(self._args.key)

    def path(self) -> str:
        return os.path.realpath(self._args.path)
