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

import cwdcontext
import os
import stat
import subprocess
import tempfile
import time

from aosptree import AOSPTree
from commandline import AOSPBuildCommandLineInterface
from configuration import Configuration
from sanity import SanityChecks


class AOSPBuild(object):
    @staticmethod
    def build(configuration: Configuration, aosp_tree: AOSPTree, product: str, variant: str, make_target: str,
              num_cores: int) -> None:
        with cwdcontext.set_cwd(aosp_tree.path()):
            # Setup environment.
            java_version = 8 if int(aosp_tree.revision().split('.')[0][len('android-'):]) >= 7 else 7
            environment_variables = {
                'CCACHE_DIR': configuration.ccache_path(),
                'JAVA_HOME': configuration.java_home(java_version),
                'USE_CCACHE_DIR': 1 if configuration.ccache_path() else 0
            }
            for variable, value in environment_variables.items():
                os.environ[variable] = str(value)
            if 'NDK_ROOT' in os.environ:
                del os.environ['NDK_ROOT']  # If NDK_ROOT is defined, the build system will try to build it (and fail).

            # Setup CCache.
            if not os.path.exists(configuration.ccache_path()):
                os.mkdir(configuration.ccache_path())
            if len(next(os.walk(configuration.ccache_path()))[-1]) == 0:  # If there are no files, CCache is not set up.
                subprocess.check_call([configuration.ccache_binary_path(), '-M', '50G'])

            # Prepare build script.
            shell_script = '#!{}\n'.format(configuration.shell())
            shell_script += 'source {}\n'.format(configuration.source_env_file_path())
            shell_script += 'lunch {}-{}\n'.format(product, variant)
            shell_script += 'make {} {}\n'.format('-j{}'.format(num_cores) if num_cores else '', make_target)

            # Build.
            AOSPBuild._exec_shell_script(shell_script)

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
    def _exec_shell_script(shell_script_content: str) -> None:
        file_path = os.path.join(tempfile.gettempdir(), 'build-{}.sh'.format(int(time.time())))
        try:
            with open(file_path, 'x') as make_build_file:
                make_build_file.write(shell_script_content)
            os.chmod(file_path, os.stat(file_path).st_mode | stat.S_IEXEC)
            subprocess.check_call([file_path])
        finally:
            # Ensure the file is always deleted.
            try:
                os.remove(file_path)
            except FileNotFoundError:
                pass


def main() -> None:
    SanityChecks.run()

    configuration = Configuration.read_configuration()
    cli = AOSPBuildCommandLineInterface(configuration)
    aosp_tree = AOSPTree(configuration, cli.path())
    print(aosp_tree)
    print(AOSPBuild.description(cli.product(), cli.variant(), cli.make_target(), cli.num_cores()))
    if cli.press_enter():
        AOSPBuild.build(configuration, aosp_tree, cli.product(), cli.variant(), cli.make_target(), cli.num_cores())


if __name__ == '__main__':
    main()
