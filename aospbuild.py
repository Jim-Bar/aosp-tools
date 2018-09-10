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

import contexts
import os
import subprocess
import sys

from aosptree import AOSPTree
from commandline import AOSPBuildCommandLineInterface
from configuration import Configuration
from sanity import SanityChecks


class AOSPBuild(object):
    """
    An :class:`AOSPBuild` is a set of AOSP build rules. Use it for building any :class:`aosptree.AOSPTree`.
    """

    _BUILDSPEC_FILE_NAME = 'buildspec.mk'

    def __init__(self, configuration: Configuration, make_target: str, product: str='', variant: str='',
                 num_cores: int=os.cpu_count()) -> None:
        self._make_target = make_target
        self._num_cores = num_cores
        self._product = product if product else configuration.default_product()
        self._variant = variant if variant else configuration.default_variant()

    def __str__(self) -> str:
        return AOSPBuild.description(self._product, self._variant, self._make_target, self._num_cores)

    def build(self, configuration: Configuration, aosp_tree: AOSPTree) -> None:
        with contexts.set_cwd(aosp_tree.path()):
            # Setup CCache.
            if not os.path.exists(configuration.ccache_path()):
                os.mkdir(configuration.ccache_path())
            if len(next(os.walk(configuration.ccache_path()))[-1]) == 0:  # If there are no files, CCache is not set up.
                subprocess.check_call([configuration.ccache_binary_path(), '-M', '50G'])

            # Setup environment then build.
            environment_variables = {
                'CCACHE_DIR': configuration.ccache_path(),
                'USE_CCACHE_DIR': str(1 if configuration.ccache_path() else 0)
            }
            build_command = ['make', self._make_target, '-j', str(self._num_cores)]
            self._generate_buildspec(aosp_tree)
            try:
                with contexts.set_variables(environment_variables):
                    # If NDK_ROOT is defined, the build system will try to build it (and fail).
                    with contexts.unset_variable('NDK_ROOT'):
                        subprocess.check_call(build_command)
            finally:
                AOSPBuild._clean_buildspec(aosp_tree)

    @staticmethod
    def description(product: str, variant: str, make_target: str, num_cores: int) -> str:
        description = list()
        description.append('Product: {}'.format(product))
        description.append('Variant: {}'.format(variant))
        description.append('Target: {}'.format(make_target))
        description.append('Number of cores: {}'.format(num_cores))
        description.append('=' * max(map(len, description)))
        description.insert(0, description[-1])

        return '\n'.join(description)

    @staticmethod
    def _clean_buildspec(aosp_tree: AOSPTree) -> None:
        if os.path.isfile(os.path.join(aosp_tree.path(), AOSPBuild._BUILDSPEC_FILE_NAME)):
            os.remove(os.path.join(aosp_tree.path(), AOSPBuild._BUILDSPEC_FILE_NAME))

    def _generate_buildspec(self, aosp_tree: AOSPTree) -> None:
        """
        Generate the ``buildspec.mk`` file for building without sourcing the environment file nor calling ``lunch``, as
        advised there: https://android.googlesource.com/platform/build/+/master/Changes.md

        :param aosp_tree: an instance of an AOSP tree.
        """
        buildspec_vars = {
            'TARGET_PRODUCT': self._product,
            'TARGET_BUILD_VARIANT': self._variant,
            'BUILD_ENV_SEQUENCE_NUMBER': 13  # Refer to build/buildspec.mk.default
        }
        buildspec_content = '\n'.join(['{}:={}'.format(name, value) for name, value in buildspec_vars.items()])

        # Avoid conflicting with existing user configuration by checking that the file does not exist.
        with open(os.path.join(aosp_tree.path(), AOSPBuild._BUILDSPEC_FILE_NAME), 'x') as buildspec_file:
            buildspec_file.write(buildspec_content)


def main() -> None:
    SanityChecks.run()

    configuration = Configuration()
    cli = AOSPBuildCommandLineInterface(configuration)
    aosp_tree = AOSPTree(cli.path())
    aosp_build = AOSPBuild(configuration, cli.make_target(), cli.product(), cli.variant(), cli.num_cores())
    print(aosp_tree)
    print(aosp_build)
    if cli.press_enter():
        aosp_build.build(configuration, aosp_tree)
    else:
        sys.exit(os.EX_USAGE)  # Set an error code for canceling chained commands.


if __name__ == '__main__':
    main()
