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

    _SECTION_AOSP_FILES = 'AOSPFiles'
    _SECTION_COMMAND_LINE_DEFAULTS = 'CommandLineDefaults'
    _SECTION_CCACHE = 'CCache'
    _SECTION_GITAMA = 'Gitama'
    _SECTION_GOOGLE_SOURCE = 'GoogleSource'
    _SECTION_JAVA_7 = 'Java7'
    _SECTION_JAVA_8 = 'Java8'
    _SECTION_LOCAL_MANIFEST = 'LocalManifest'
    _SECTION_REPO = 'Repo'
    _SECTION_REPOSITORY_AVB = 'RepositoryAvb'
    _SECTION_REPOSITORY_BUILD = 'RepositoryBuild'
    _SECTION_REPOSITORY_LOCAL_MANIFEST = 'RepositoryLocalManifest'
    _SECTION_REPOSITORY_MANIFEST = 'RepositoryManifest'
    _SECTION_SHELL = 'Shell'
    _SECTION_SIGNING_INFO = 'SigningInfo'
    _SECTION_VARIANTS = 'Variants'

    _OPTION_BINARY_PATH = 'BinaryPath'
    _OPTION_DEPTH = 'Depth'
    _OPTION_GENERIC_REF = 'GenericRef'
    _OPTION_GROUPS = 'Groups'
    _OPTION_LIST = 'List'
    _OPTION_TEMPLATE_NAME = 'TemplateName'
    _OPTION_MAKE_TARGET = 'MakeTarget'
    _OPTION_NAME = 'Name'
    _OPTION_PREFIX_FORMAT = 'PrefixFormat'
    _OPTION_NO_TAGS = 'NoTags'
    _OPTION_NUM_CORES = 'NumCores'
    _OPTION_ONLY_CURRENT_BRANCH = 'OnlyCurrentBranch'
    _OPTION_PATH = 'Path'
    _OPTION_PRODUCT = 'Product'
    _OPTION_PROTOCOL = 'Protocol'
    _OPTION_SOURCE_ENV_FILE_PATH = 'SourceEnvFilePath'
    _OPTION_SPECIFIC_REF = 'SpecificRef'
    _OPTION_TRACE = 'Trace'
    _OPTION_VARIANT = 'Variant'
    _OPTION_URL = 'Url'
    _OPTION_USER = 'User'

    def __init__(self, default_config_file_name: str, config_file_names: List[str]) -> None:
        configparser.ConfigParser.__init__(self, interpolation=None)

        with open(default_config_file_name) as default_config_file:
            self.read_file(default_config_file)
        self.read(config_file_names)

        self._default_generic_ref = self.get(Configuration._SECTION_COMMAND_LINE_DEFAULTS,
                                             Configuration._OPTION_GENERIC_REF)
        self._default_make_target = self.get(Configuration._SECTION_COMMAND_LINE_DEFAULTS,
                                             Configuration._OPTION_MAKE_TARGET)
        self._default_num_cores = self.getint(Configuration._SECTION_COMMAND_LINE_DEFAULTS,
                                              Configuration._OPTION_NUM_CORES)
        self._default_path = self.get(Configuration._SECTION_COMMAND_LINE_DEFAULTS, Configuration._OPTION_PATH)
        self._default_prefix = time.strftime(self.get(Configuration._SECTION_COMMAND_LINE_DEFAULTS,
                                                      Configuration._OPTION_PREFIX_FORMAT))
        self._default_product = self.get(Configuration._SECTION_COMMAND_LINE_DEFAULTS, Configuration._OPTION_PRODUCT)
        self._default_specific_ref = self.get(Configuration._SECTION_COMMAND_LINE_DEFAULTS,
                                              Configuration._OPTION_SPECIFIC_REF)
        self._default_variant = self.get(Configuration._SECTION_COMMAND_LINE_DEFAULTS, Configuration._OPTION_VARIANT)

        protocol = self.get(Configuration._SECTION_GOOGLE_SOURCE, Configuration._OPTION_PROTOCOL)
        user = self.get(Configuration._SECTION_GOOGLE_SOURCE, Configuration._OPTION_USER)
        url = self.get(Configuration._SECTION_GOOGLE_SOURCE, Configuration._OPTION_URL)
        path = self.get(Configuration._SECTION_REPOSITORY_AVB, Configuration._OPTION_PATH)
        name = self.get(Configuration._SECTION_REPOSITORY_AVB, Configuration._OPTION_NAME)
        self._repository_avb = Repository(protocol, user, url, path, name)

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

        protocol = self.get(Configuration._SECTION_GOOGLE_SOURCE, Configuration._OPTION_PROTOCOL)
        user = self.get(Configuration._SECTION_GOOGLE_SOURCE, Configuration._OPTION_USER)
        url = self.get(Configuration._SECTION_GOOGLE_SOURCE, Configuration._OPTION_URL)
        path = self.get(Configuration._SECTION_REPOSITORY_MANIFEST, Configuration._OPTION_PATH)
        name = self.get(Configuration._SECTION_REPOSITORY_MANIFEST, Configuration._OPTION_NAME)
        self._repository_manifest = Repository(protocol, user, url, path, name)

        self._ccache_bin_path = self.get(Configuration._SECTION_CCACHE, Configuration._OPTION_BINARY_PATH)
        self._ccache_path = self.get(Configuration._SECTION_CCACHE, Configuration._OPTION_PATH)
        self._java_7_path = self.get(Configuration._SECTION_JAVA_7, Configuration._OPTION_PATH)
        self._java_8_path = self.get(Configuration._SECTION_JAVA_8, Configuration._OPTION_PATH)
        self._local_manifest_dir = self.get(Configuration._SECTION_LOCAL_MANIFEST, Configuration._OPTION_PATH)
        self._local_manifest_file = self.get(Configuration._SECTION_LOCAL_MANIFEST, Configuration._OPTION_NAME)
        self._local_manifest_template_file = self.get(Configuration._SECTION_LOCAL_MANIFEST,
                                                      Configuration._OPTION_TEMPLATE_NAME)
        self._repo_depth = self.getint(Configuration._SECTION_REPO, Configuration._OPTION_DEPTH)
        self._repo_groups = self.get(Configuration._SECTION_REPO, Configuration._OPTION_GROUPS).split()
        self._repo_no_tags = self.getboolean(Configuration._SECTION_REPO, Configuration._OPTION_NO_TAGS)
        self._repo_only_current_branch = self.getboolean(Configuration._SECTION_REPO,
                                                         Configuration._OPTION_ONLY_CURRENT_BRANCH)
        self._repo_trace = self.getboolean(Configuration._SECTION_REPO, Configuration._OPTION_TRACE)
        self._shell = self.get(Configuration._SECTION_SHELL, Configuration._OPTION_PATH)
        self._signing_info = self.get(Configuration._SECTION_SIGNING_INFO, Configuration._OPTION_PATH)
        self._source_env_file_path = self.get(Configuration._SECTION_AOSP_FILES,
                                              Configuration._OPTION_SOURCE_ENV_FILE_PATH)
        self._variants_names = self.get(Configuration._SECTION_VARIANTS, Configuration._OPTION_LIST).split()

    @staticmethod
    def read_configuration() -> 'Configuration':
        # Read the configuration file.
        default_configuration_file_name = 'default_config.ini'
        configuration_file_names = ['config.ini']
        return Configuration(default_configuration_file_name, configuration_file_names)

    def ccache_binary_path(self) -> str:
        return self._ccache_bin_path

    def ccache_path(self) -> str:
        return self._ccache_path

    def default_generic_ref(self) -> str:
        return self._default_generic_ref

    def default_prefix(self) -> str:
        return self._default_prefix

    def default_make_target(self) -> str:
        return self._default_make_target

    def default_num_cores(self) -> int:
        return self._default_num_cores

    def default_path(self) -> str:
        return self._default_path

    def default_product(self) -> str:
        return self._default_product

    def default_specific_ref(self) -> str:
        return self._default_specific_ref

    def default_variant(self) -> str:
        return self._default_variant

    def java_home(self, java_version: int) -> str:
        if java_version == 7:
            return self._java_7_path
        elif java_version == 8:
            return self._java_8_path
        else:
            raise ValueError('Invalid Java version: {}'.format(java_version))

    def local_manifest_directory(self) -> str:
        return self._local_manifest_dir

    def local_manifest_file(self) -> str:
        return self._local_manifest_file

    def local_manifest_template_file(self) -> str:
        return self._local_manifest_template_file

    def repo_depth(self) -> int:
        return self._repo_depth

    def repo_groups(self) -> List[str]:
        return self._repo_groups

    def repo_no_tags(self) -> bool:
        return self._repo_no_tags

    def repo_only_current_branch(self) -> bool:
        return self._repo_only_current_branch

    def repo_trace(self) -> List[str]:
        return self._repo_trace

    def repository_avb(self) -> Repository:
        return self._repository_avb

    def repository_build(self) -> Repository:
        return self._repository_build

    def repository_local_manifest(self) -> Repository:
        return self._repository_local_manifest

    def repository_manifest(self) -> Repository:
        return self._repository_manifest

    def shell(self) -> str:
        return self._shell

    def signing_info(self) -> str:
        return self._signing_info

    def source_env_file_path(self) -> str:
        return self._source_env_file_path

    def variants(self) -> List[str]:
        return self._variants_names
