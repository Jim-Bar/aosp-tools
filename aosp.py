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

import hashlib
import os
import randomstring
import shutil
import stat
import subprocess
import sys
import tempfile

from commandline import CommandLineAdapter
from configuration import Configuration
from manifest import LocalManifest
from repo import RepoAdapter
from typing import List


class BuildOptions(object):
    """
    All the characteristics for the build of an AOSP.
    """

    def __init__(self, num_cores: int, ota_package: bool, update_package: bool) -> None:
        if num_cores == 0:  # Resolve the real number of available cores.
            num_cores = int(subprocess.check_output(['nproc']))
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
        description += '{}\n'.format('=' * len('Path: {}'.format(self._path)))
        description += 'Path: {}\n'.format(self._path)
        description += 'Release: {}\n'.format(self._release)
        description += 'Variant: {}\n'.format(self._variant)
        description += 'Device: {}\n'.format(self._device)
        description += 'Java version: {}\n'.format(self._java_version)
        description += 'Version: {}\n'.format(self._version)
        description += 'Project: {}\n'.format(self._project)
        description += 'Generic ref: {}\n'.format(self._generic_ref)
        description += 'Specific ref: {}\n'.format(self._specific_ref)
        description += '=' * len('Path: {}'.format(self._path))

        return description

    def device(self) -> str:
        return self._device

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

    def variant(self) -> str:
        return self._variant

    def version(self) -> str:
        return self._version


class AOSP(object):
    """
    Clone, build and flash an Android Open Source Project.
    """

    def __init__(self, environment: AOSPEnvironment) -> None:
        self._environment = environment

    def build_droid(self, configuration: Configuration, build_options: BuildOptions) -> None:
        file_content = '#!{}\n'.format(configuration.shell())
        file_content += 'source {}\n'.format(configuration.source_env_file_name())
        file_content += 'lunch aosp_{}-{}\n'.format(self._environment.device(), self._environment.variant())
        file_content += 'make {} droid\n'.format('-j{}'.format(build_options.num_cores())
                                                 if build_options.num_cores() else '')

        AOSP._exec_file('{}.sh'.format(randomstring.random_string(min_length=10, max_length=10, digits=True)),
                        file_content)

    def build_ota_package(self, configuration: Configuration, build_options: BuildOptions) -> None:
        pass  # TODO: do.

    def build_update_package(self, configuration: Configuration, build_options: BuildOptions) -> None:
        file_content = '#!{}\n'.format(configuration.shell())
        file_content += 'source {}\n'.format(configuration.source_env_file_name())
        file_content += 'lunch aosp_{}-{}\n'.format(self._environment.device(), self._environment.variant())
        file_content += 'make {} updatepackage\n'.format('-j{}'.format(build_options.num_cores())
                                                         if build_options.num_cores() else '')

    def clone(self, configuration: Configuration, build_options: BuildOptions) -> None:
        self._create(configuration, build_options)
        self._fetch_manifest(configuration)
        self._fetch_local_manifest(configuration)
        RepoAdapter.sync()
        self._setup_ccache(configuration)

    def export_to_delivery_directory(self, configuration: Configuration) -> None:
        os.makedirs(self._delivery_directory(configuration))
        self._export_built_files_to_delivery_directory(configuration)
        self._export_firmwares_files_to_delivery_directory(configuration)
        self._compute_hashes(configuration)
        self._export_flash_script(configuration)

    def _compute_hashes(self, configuration: Configuration) -> None:
        for file_name in os.listdir(self._delivery_directory(configuration)):
            if file_name.split('.').pop() in ['img', 'zip']:
                with open(os.path.join(self._delivery_directory(configuration), file_name), 'rb') as hashed_file:
                    hash_file_name = os.path.join(self._delivery_directory(configuration), '{}.md5'.format(file_name))
                    with open(hash_file_name, 'x') as hash_file:
                        hash_file.write(hashlib.md5(hashed_file.read()).hexdigest())
                    hash_file_name = os.path.join(self._delivery_directory(configuration),
                                                  '{}.sha512'.format(file_name))
                    with open(hash_file_name, 'x') as hash_file:
                        hash_file.write(hashlib.sha512(hashed_file.read()).hexdigest())

    def _create(self, configuration: Configuration, build_options: BuildOptions) -> None:
        if not os.path.exists(configuration.ccache_path()):
            os.mkdir(configuration.ccache_path())

        os.mkdir(self._environment.path())
        os.chdir(self._environment.path())

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

    def _delivery_directory(self, configuration: Configuration) -> str:
        return os.path.join(configuration.base_delivery_directory(), self._environment.variant())

    @staticmethod
    def _exec_file(file_name: str, file_content: str) -> None:
        try:
            with open(file_name, 'x') as make_build_file:
                make_build_file.write(file_content)
            os.chmod(file_name, os.stat(file_name).st_mode | stat.S_IEXEC)
            subprocess.check_call(['./{}'.format(file_name)])
        finally:
            # Ensure the file is always deleted.
            try:
                os.remove(file_name)
            except FileNotFoundError:
                pass

    def _export_built_files_to_delivery_directory(self, configuration: Configuration) -> None:
        out_directory = os.path.join('out', 'target', 'product', self._environment.device())
        for file_name in os.listdir(out_directory):
            if file_name.split('.')[-1] in ['img', 'zip'] or file_name in configuration.files_to_include_in_delivery():
                shutil.copy(os.path.join(out_directory, file_name), self._delivery_directory(configuration))

        if os.path.exists(configuration.dist_directory()):
            shutil.copy(configuration.dist_directory(), os.path.join(self._delivery_directory(configuration), 'dist'))

    def _export_firmwares_files_to_delivery_directory(self, configuration: Configuration) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            configuration.repository_firmwares().clone(os.path.dirname(temp_directory),
                                                       os.path.basename(temp_directory))
            configuration.repository_firmwares().checkout(self._environment.specific_ref())
            for file_name in os.listdir(temp_directory):
                if file_name.split('.').pop() == 'img':
                    shutil.move(os.path.join(temp_directory, file_name), self._delivery_directory(configuration))

    def _export_flash_script(self, configuration: Configuration) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            configuration.repository_system_scripts_tools().clone(os.path.dirname(temp_directory),
                                                                  os.path.basename(temp_directory))
            shutil.move(os.path.join(temp_directory, configuration.flash_script_path()),
                        self._delivery_directory(configuration))

    def _fetch_local_manifest(self, configuration: Configuration) -> None:
        local_manifest_path = os.path.join(RepoAdapter.INSTALL_DIRECTORY, configuration.local_manifest_directory())
        os.mkdir(local_manifest_path)

        local_manifest = LocalManifest.from_revisions(configuration, self._environment.generic_ref(),
                                                      self._environment.specific_ref())
        local_manifest.to_file(os.path.join(local_manifest_path, configuration.local_manifest_file()))

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
    environment = AOSPEnvironment(cli.path(), cli.name(), cli.release(), cli.variant(), cli.device(),
                                  cli.specific_ref(), cli.generic_ref(), cli.version(), cli.project())
    print(environment)
    if not cli.continue_when_prompted():
        try:
            input('Press enter to continue...')
        except KeyboardInterrupt:
            print('')
            return
    aosp = AOSP(environment)
    options = BuildOptions(cli.num_cores(), cli.ota_package(), cli.update_package())
    aosp.clone(configuration, options)
    if cli.build():
        aosp.build_droid(configuration, options)
    if cli.update_package():
        aosp.build_update_package(configuration, options)
    if cli.ota_package():
        aosp.build_ota_package(configuration, options)
    if cli.build() or cli.update_package() or cli.ota_package():
        aosp.export_to_delivery_directory(configuration)


if __name__ == '__main__':
    main()
