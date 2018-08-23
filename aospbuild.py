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
    @staticmethod
    def build(configuration: Configuration, aosp_tree: AOSPTree, make_target: str, product: str='', variant: str='',
              num_cores: int=os.cpu_count()) -> None:
        with contexts.set_cwd(aosp_tree.path()):
            # Setup CCache.
            if not os.path.exists(configuration.ccache_path()):
                os.mkdir(configuration.ccache_path())
            if len(next(os.walk(configuration.ccache_path()))[-1]) == 0:  # If there are no files, CCache is not set up.
                subprocess.check_call([configuration.ccache_binary_path(), '-M', '50G'])

            # Prepare build script.
            shell_script = 'set -e\n'
            shell_script += 'source {}\n'.format(configuration.source_env_file_path())
            shell_script += 'lunch {}-{}\n'.format(product if product else configuration.default_product(),
                                                   variant if variant else configuration.default_variant())
            shell_script += 'make {} {}\n'.format('-j{}'.format(num_cores) if num_cores else '', make_target)

            # Setup environment then build.
            java_version = 8 if int(aosp_tree.revision().split('.')[0][len('android-'):]) >= 7 else 7
            environment_variables = {
                'CCACHE_DIR': configuration.ccache_path(),
                'JAVA_HOME': configuration.java_home(java_version),
                'USE_CCACHE_DIR': str(1 if configuration.ccache_path() else 0)
            }
            with contexts.set_variables(environment_variables):
                # If NDK_ROOT is defined, the build system will try to build it (and fail).
                with contexts.unset_variable('NDK_ROOT'):
                    subprocess.run(['bash'], input=shell_script.encode(), check=True)

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


def main() -> None:
    SanityChecks.run()

    configuration = Configuration()
    cli = AOSPBuildCommandLineInterface(configuration)
    aosp_tree = AOSPTree(configuration, cli.path())
    print(aosp_tree)
    print(AOSPBuild.description(cli.product(), cli.variant(), cli.make_target(), cli.num_cores()))
    if cli.press_enter():
        AOSPBuild.build(configuration, aosp_tree, cli.make_target(), cli.product(), cli.variant(), cli.num_cores())
    else:
        sys.exit(os.EX_USAGE)  # Set an error code for canceling chained commands.


if __name__ == '__main__':
    main()
