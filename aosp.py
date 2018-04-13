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
import subprocess
import sys

from commandline import CommandLineAdapter
from configuration import Configuration
from repo import RepoAdapter
from typing import List


class BuildOptions(object):
    """
    All the characteristics for the build of an AOSP.
    """

    def __init__(self, num_cores: int, ota_package: bool, update_package: bool) -> None:
        self._num_cores = num_cores
        self._ota_package = ota_package
        self._update_package = update_package

    def num_cores(self) -> int:
        return self._num_cores

    def ota_package(self) -> bool:
        return self._ota_package

    def update_package(self) -> bool:
        return self._update_package


class AOSPEnvironment(object):
    """
    All the characteristics of an Android Open Source Project.
    """

    def __init__(self, path: str, prefix: str, release: str, variant: str, device: str, specific_ref: str,
                 generic_ref: str, version: str, project: str) -> None:
        self._path = os.path.join(os.path.realpath(path), '{}_{}_{}_{}'.format(prefix, release, variant, device))
        self._release = release
        self._variant = variant
        self._device = device
        self._specific_ref = specific_ref
        self._generic_ref = generic_ref
        self._version = version
        self._project = project
        self._java_version = 8 if int(self._release.split('.')[0][len('android-'):]) >= 7 else 7

        # Sanity checks.
        if not sys.platform.startswith('linux'):
            raise RuntimeError('Must be on Linux')
        if os.getuid() == 0:
            raise RuntimeError('Must not be root')
        RepoAdapter.sanity_check()

    def __str__(self) -> str:
        description = ''
        description += 'Path: {}\n'.format(self._path)
        description += 'Release: {}\n'.format(self._release)
        description += 'Variant: {}\n'.format(self._variant)
        description += 'Device: {}\n'.format(self._device)
        description += 'Java version: {}\n'.format(self._java_version)
        description += 'Version: {}\n'.format(self._version)
        description += 'Project: {}\n'.format(self._project)
        description += 'Generic ref: {}\n'.format(self._generic_ref)
        description += 'Specific ref: {}'.format(self._specific_ref)

        return description

    def generic_ref(self) -> str:
        return self._generic_ref

    def java_version(self) -> int:
        return self._java_version

    def path(self) -> str:
        return self._path

    def project(self) -> str:
        return self._project

    def release(self) -> str:
        return self._release

    def specific_ref(self) -> str:
        return self._specific_ref

    def version(self) -> str:
        return self._version


class AOSP(object):
    """
    Clone, build and flash an Android Open Source Project.
    """

    def __init__(self, environment: AOSPEnvironment) -> None:
        self._environment = environment
        print(environment)  # FIXME: Move/Remove.

    def build(self):
        pass

    def clone(self, configuration: Configuration, build_options: BuildOptions) -> None:
        self._create(configuration, build_options)
        self._fetch_manifest(configuration)
        self._fetch_local_manifest(configuration)
        RepoAdapter.sync()
        self._setup_ccache(configuration)

    def _create(self, configuration: Configuration, build_options: BuildOptions) -> None:
        if not os.path.exists(configuration.ccache_path()):
            os.mkdir(configuration.ccache_path())

        os.mkdir(self._environment.path())
        os.chdir(self._environment.path())

        os.mkdir(configuration.final_output_directory())

        # Create the source file for later uses.
        environment_variables = self._environment_variables(configuration,
                                                            configuration.java_home(self._environment.java_version()),
                                                            build_options.num_cores())
        with open(os.path.join(self._environment.path(), configuration.source_env_file_name()), 'w') as source_env_file:
            # Environment variables.
            for variable, value in environment_variables.items():
                source_env_file.write('export {}={}\n'.format(variable, value))

            # The AOSP's environment variables.
            source_env_file.write(' '.join(self._source_env_setup_cmd()))

    def _fetch_local_manifest(self, configuration: Configuration) -> None:
        configuration.repository_local_manifest().clone(RepoAdapter.INSTALL_DIRECTORY,
                                                        configuration.local_manifest_directory())
        configuration.repository_local_manifest().checkout(self._environment.specific_ref())

        local_manifest_path = os.path.join(RepoAdapter.INSTALL_DIRECTORY, configuration.local_manifest_directory(),
                                           configuration.local_manifest_file())
        with open(local_manifest_path) as local_manifest_file:
            local_manifest_content = local_manifest_file.read()

        tags = configuration.repository_local_manifest().get_tags()
        if self._environment.specific_ref() in tags:
            ref_type = 'tags'
        else:
            ref_type = 'heads'

        local_manifest_content = local_manifest_content.replace('@TYPE@', ref_type)
        local_manifest_content = local_manifest_content.replace('@GENERIC_VERSION@', self._environment.generic_ref())
        local_manifest_content = local_manifest_content.replace('@SPECIFIC_VERSION@', self._environment.specific_ref())

        with open(local_manifest_path, 'w') as local_manifest_file:
            local_manifest_file.write(local_manifest_content)

    def _fetch_manifest(self, configuration: Configuration) -> None:
        RepoAdapter.init(configuration.repository_manifest().get_remote_url(), self._environment.release(),
                         configuration.repo_groups())

    def _environment_variables(self, configuration: Configuration, java_home: str, num_cores: int) -> dict:
        variables = {
            'CCACHE_DIR': configuration.ccache_path(),
            'JAVA_HOME': java_home,
            'NBCORE': num_cores,
            'REPO_TRACE': 1 if configuration.repo_trace() else 0,
            'USE_CCACHE_DIR': 1 if configuration.ccache_path() else 0,
            'WEBUI_IMAGE_VERSION': self._environment.release(),
            'WEBUI_PLATFORM': self._environment.project(),
            'WEBUI_VERSION_NUM': self._environment.version()
        }

        return variables

    @staticmethod
    def _setup_ccache(configuration: Configuration) -> None:
        if len(next(os.walk(configuration.ccache_path()))) == 0:  # If there are no files, CCache is not set up yet.
            subprocess.check_call([configuration.ccache_binary_path(), '-M', '50G'])

    def _source_env_setup_cmd(self) -> List[str]:
        return ['.', os.path.join(self._environment.path(), 'build/envsetup.sh')]


def main():
    configuration = Configuration.read_configuration()
    cli = CommandLineAdapter(configuration)
    aosp = AOSP(AOSPEnvironment(cli.path(), cli.name(), cli.release(), cli.variant(), cli.device(), cli.specific_ref(),
                                cli.generic_ref(), cli.version(), cli.project()))
    aosp.clone(configuration, BuildOptions(cli.num_cores(), cli.ota_package(), cli.update_package()))
    aosp.build()


if __name__ == '__main__':
    main()
