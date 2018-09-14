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

import configparser
import contexts
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
    _SECTION_LOCAL_MANIFEST = 'LocalManifest'
    _SECTION_REPO = 'Repo'
    _SECTION_REPOSITORY_AVB = 'RepositoryAvb'
    _SECTION_REPOSITORY_BUILD = 'RepositoryBuild'
    _SECTION_REPOSITORY_LOCAL_MANIFEST = 'RepositoryLocalManifest'
    _SECTION_REPOSITORY_MANIFEST = 'RepositoryManifest'
    _SECTION_SIGNING_INFO = 'SigningInfo'
    _SECTION_VARIANTS = 'Variants'
    _SECTION_VENDORS = 'Vendors'

    _OPTION_BINARY_PATH = 'BinaryPath'
    _OPTION_BUILDSPEC_PATH = 'BuildspecPath'
    _OPTION_DEPTH = 'Depth'
    _OPTION_DIST_PATH = 'DistPath'
    _OPTION_FLASH_SYSTEM_IMAGE_PATH = 'FlashSystemImagePath'
    _OPTION_FLASH_VBMETA_IMAGE_PATH = 'FlashVBMetaImagePath'
    _OPTION_GENERIC_REF = 'GenericRef'
    _OPTION_GROUPS = 'Groups'
    _OPTION_HOST_BIN_PATH = 'HostBinPath'
    _OPTION_LINK = 'Link'
    _OPTION_LIST = 'List'
    _OPTION_TEMPLATE_NAME = 'TemplateName'
    _OPTION_MAKE_TARGET = 'MakeTarget'
    _OPTION_NAME = 'Name'
    _OPTION_NAME_FORMAT = 'NameFormat'
    _OPTION_NO_TAGS = 'NoTags'
    _OPTION_NUM_CORES = 'NumCores'
    _OPTION_ONLY_CURRENT_BRANCH = 'OnlyCurrentBranch'
    _OPTION_PATH = 'Path'
    _OPTION_PRODUCT = 'Product'
    _OPTION_PROTOCOL = 'Protocol'
    _OPTION_RELEASE_TOOLS = 'ReleaseTools'
    _OPTION_SPECIFIC_REF = 'SpecificRef'
    _OPTION_TRACE = 'Trace'
    _OPTION_VARIANT = 'Variant'
    _OPTION_VERIFY_TIMEOUT_SEC = 'VerifyTimeoutSec'
    _OPTION_URL = 'Url'
    _OPTION_USER = 'User'

    def __init__(self) -> None:
        configparser.ConfigParser.__init__(self, interpolation=None)

        default_config_file_name = 'default_config.ini'
        config_file_names = ['config.ini']
        with contexts.open_local(default_config_file_name) as default_config_file:
            self.read_file(default_config_file)
        self.read(config_file_names)

        self._default_flash_system_path = self.get(Configuration._SECTION_COMMAND_LINE_DEFAULTS,
                                                   Configuration._OPTION_FLASH_SYSTEM_IMAGE_PATH)
        self._default_flash_vbmeta_path = self.get(Configuration._SECTION_COMMAND_LINE_DEFAULTS,
                                                   Configuration._OPTION_FLASH_VBMETA_IMAGE_PATH)
        self._default_generic_ref = self.get(Configuration._SECTION_COMMAND_LINE_DEFAULTS,
                                             Configuration._OPTION_GENERIC_REF)
        self._default_make_target = self.get(Configuration._SECTION_COMMAND_LINE_DEFAULTS,
                                             Configuration._OPTION_MAKE_TARGET)
        self._default_num_cores = self.getint(Configuration._SECTION_COMMAND_LINE_DEFAULTS,
                                              Configuration._OPTION_NUM_CORES)
        self._default_path = self.get(Configuration._SECTION_COMMAND_LINE_DEFAULTS, Configuration._OPTION_PATH)
        self._default_name = time.strftime(self.get(Configuration._SECTION_COMMAND_LINE_DEFAULTS,
                                                    Configuration._OPTION_NAME_FORMAT))
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

        self._buildspec_path = self.get(Configuration._SECTION_AOSP_FILES, Configuration._OPTION_BUILDSPEC_PATH)
        self._ccache_bin_path = self.get(Configuration._SECTION_CCACHE, Configuration._OPTION_BINARY_PATH)
        self._ccache_path = self.get(Configuration._SECTION_CCACHE, Configuration._OPTION_PATH)
        self._dist_path = self.get(Configuration._SECTION_AOSP_FILES, Configuration._OPTION_DIST_PATH)
        self._host_bin_path = self.get(Configuration._SECTION_AOSP_FILES, Configuration._OPTION_HOST_BIN_PATH)
        self._local_manifest_dir = self.get(Configuration._SECTION_LOCAL_MANIFEST, Configuration._OPTION_PATH)
        self._local_manifest_file = self.get(Configuration._SECTION_LOCAL_MANIFEST, Configuration._OPTION_NAME)
        self._local_manifest_template_file = self.get(Configuration._SECTION_LOCAL_MANIFEST,
                                                      Configuration._OPTION_TEMPLATE_NAME)
        self._release_tools_path = self.get(Configuration._SECTION_AOSP_FILES, Configuration._OPTION_RELEASE_TOOLS)
        self._repo_depth = self.getint(Configuration._SECTION_REPO, Configuration._OPTION_DEPTH)
        self._repo_groups = self.get(Configuration._SECTION_REPO, Configuration._OPTION_GROUPS).split()
        self._repo_no_tags = self.getboolean(Configuration._SECTION_REPO, Configuration._OPTION_NO_TAGS)
        self._repo_only_current_branch = self.getboolean(Configuration._SECTION_REPO,
                                                         Configuration._OPTION_ONLY_CURRENT_BRANCH)
        self._repo_trace = self.getboolean(Configuration._SECTION_REPO, Configuration._OPTION_TRACE)
        self._signing_info = self.get(Configuration._SECTION_SIGNING_INFO, Configuration._OPTION_PATH)
        self._variants_names = self.get(Configuration._SECTION_VARIANTS, Configuration._OPTION_LIST).split()
        self._vendors_link = self.get(Configuration._SECTION_VENDORS, Configuration._OPTION_LINK)
        self._vendors_path = self.get(Configuration._SECTION_VENDORS, Configuration._OPTION_PATH)
        self._verify_timeout_sec = self.getint(Configuration._SECTION_SIGNING_INFO,
                                               Configuration._OPTION_VERIFY_TIMEOUT_SEC)

    def buildspec_path(self) -> str:
        return self._buildspec_path

    def ccache_binary_path(self) -> str:
        return self._ccache_bin_path

    def ccache_path(self) -> str:
        return self._ccache_path

    def default_flash_system_path(self) -> str:
        return self._default_flash_system_path

    def default_flash_vbmeta_path(self) -> str:
        return self._default_flash_vbmeta_path

    def default_generic_ref(self) -> str:
        return self._default_generic_ref

    def default_make_target(self) -> str:
        return self._default_make_target

    def default_name(self) -> str:
        return self._default_name

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

    def dist_path(self) -> str:
        return self._dist_path

    def host_bin_path(self) -> str:
        return self._host_bin_path

    def local_manifest_directory(self) -> str:
        return self._local_manifest_dir

    def local_manifest_file(self) -> str:
        return self._local_manifest_file

    def local_manifest_template_file(self) -> str:
        return self._local_manifest_template_file

    def release_tools_path(self) -> str:
        return self._release_tools_path

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

    def signing_info(self) -> str:
        return self._signing_info

    def variants(self) -> List[str]:
        return self._variants_names

    def vendors_link(self) -> str:
        return self._vendors_link

    def vendors_path(self) -> str:
        return self._vendors_path

    def verify_timeout_sec(self) -> int:
        return self._verify_timeout_sec
