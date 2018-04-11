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

import configparser
import time

from git import Repository
from typing import List


class Configuration(configparser.ConfigParser):
    """
    Read the default configuration file, and optionally the additional overriding configuration files if any.
    """

    _SECTION_COMMAND_LINE_DEFAULTS = 'CommandLineDefaults'
    _SECTION_DEVICES = 'Devices'
    _SECTION_GITAMA = 'Gitama'
    _SECTION_GOOGLE_SOURCE = 'GoogleSource'
    _SECTION_PROFILES = 'Profiles'
    _SECTION_PROJECTS = 'Projects'
    _SECTION_REPOSITORY_BUILD = 'RepositoryBuild'
    _SECTION_REPOSITORY_LOCAL_MANIFEST = 'RepositoryLocalManifest'

    _OPTION_DEVICE = 'Device'
    _OPTION_GENERIC_REF = 'GenericRef'
    _OPTION_LIST = 'List'
    _OPTION_NAME = 'Name'
    _OPTION_NAME_FORMAT = 'NameFormat'
    _OPTION_PATH = 'Path'
    _OPTION_PROFILE = 'Profile'
    _OPTION_PROJECT = 'Project'
    _OPTION_PROTOCOL = 'Protocol'
    _OPTION_SPECIFIC_REF = 'SpecificRef'
    _OPTION_URL = 'Url'
    _OPTION_USER = 'User'

    def __init__(self, default_config_file_name: str, config_file_names: List[str]) -> None:
        configparser.ConfigParser.__init__(self, interpolation=None)

        with open(default_config_file_name) as default_config_file:
            self.read_file(default_config_file)
        self.read(config_file_names)

        self._default_device = self.get(Configuration._SECTION_COMMAND_LINE_DEFAULTS, Configuration._OPTION_DEVICE)
        self._default_generic_ref = self.get(Configuration._SECTION_COMMAND_LINE_DEFAULTS,
                                             Configuration._OPTION_GENERIC_REF)
        self._default_name = time.strftime(self.get(Configuration._SECTION_COMMAND_LINE_DEFAULTS,
                                                    Configuration._OPTION_NAME_FORMAT))
        self._default_path = self.get(Configuration._SECTION_COMMAND_LINE_DEFAULTS, Configuration._OPTION_PATH)
        self._default_project = self.get(Configuration._SECTION_COMMAND_LINE_DEFAULTS, Configuration._OPTION_PROJECT)
        self._default_profile = self.get(Configuration._SECTION_COMMAND_LINE_DEFAULTS, Configuration._OPTION_PROFILE)
        self._default_specific_ref = self.get(Configuration._SECTION_COMMAND_LINE_DEFAULTS,
                                              Configuration._OPTION_SPECIFIC_REF)

        protocol = self.get(Configuration._SECTION_GOOGLE_SOURCE, Configuration._OPTION_PROTOCOL)
        user = self.get(Configuration._SECTION_GOOGLE_SOURCE, Configuration._OPTION_USER)
        url = self.get(Configuration._SECTION_GOOGLE_SOURCE, Configuration._OPTION_URL)
        path = self.get(Configuration._SECTION_REPOSITORY_BUILD, Configuration._OPTION_PATH)
        name = self.get(Configuration._SECTION_REPOSITORY_BUILD, Configuration._OPTION_NAME)
        self._repository_build = Repository(protocol, user, url, path, name)

        protocol = self.get(Configuration._SECTION_GITAMA, Configuration._OPTION_PROTOCOL)
        user = self.get(Configuration._SECTION_GITAMA, Configuration._OPTION_USER)
        url = self.get(Configuration._SECTION_GITAMA, Configuration._OPTION_URL)
        path = self.get(Configuration._SECTION_REPOSITORY_LOCAL_MANIFEST, Configuration._OPTION_PATH)
        name = self.get(Configuration._SECTION_REPOSITORY_LOCAL_MANIFEST, Configuration._OPTION_NAME)
        self._repository_local_manifest = Repository(protocol, user, url, path, name)

        self._devices_names = self.get(Configuration._SECTION_DEVICES, Configuration._OPTION_LIST).split()
        self._profiles_names = self.get(Configuration._SECTION_PROFILES, Configuration._OPTION_LIST).split()
        self._projects_names = self.get(Configuration._SECTION_PROJECTS, Configuration._OPTION_LIST).split()

    @staticmethod
    def read_configuration() -> 'Configuration':
        # Read the configuration file.
        default_configuration_file_name = 'default_config.ini'
        configuration_file_names = ['config.ini']
        return Configuration(default_configuration_file_name, configuration_file_names)

    def default_device(self) -> str:
        return self._default_device

    def default_generic_ref(self) -> str:
        return self._default_generic_ref

    def default_name(self) -> str:
        return self._default_name

    def default_path(self) -> str:
        return self._default_path

    def default_project(self) -> str:
        return self._default_project

    def default_profile(self) -> str:
        return self._default_profile

    def default_specific_ref(self) -> str:
        return self._default_specific_ref

    def devices(self) -> List[str]:
        return self._devices_names

    def profiles(self) -> List[str]:
        return self._profiles_names

    def projects(self) -> List[str]:
        return self._projects_names

    def repository_build(self) -> Repository:
        return self._repository_build

    def repository_local_manifest(self) -> Repository:
        return self._repository_local_manifest
