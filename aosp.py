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

from configuration import Configuration
from git import GitConfiguration, GitUtils


class AOSP(object):
    """
    Clone, build and flash an Android Open Source Project.
    """


class AOSPEnvironment(object):
    """
    All the characteristics of an Android Open Source Project.
    """

    def __init__(self, configuration: Configuration, path: str, name: str, release: str, profile: str, device: str,
                 specific_ref: str, generic_ref: str, version: str, project: str) -> None:
        self._path = os.path.realpath(path)
        self._name = name
        self._release = release
        self._profile = profile
        self._device = device
        self._specific_ref = specific_ref
        self._generic_ref = generic_ref
        self._version = version
        self._project = project

        # Sanity checks.
        assert os.path.exists(self._path)
        _, tags = GitUtils.remote_refs(configuration.repository_build().path(),
                                       configuration.repository_build().name(),
                                       configuration.git_configuration_google_source())
        assert self._release in tags
        assert self._profile in configuration.profiles()
        assert self._device in configuration.devices()
        heads, tags = GitUtils.remote_refs(configuration.repository_local_manifest().path(),
                                           configuration.repository_local_manifest().name(),
                                           configuration.git_configuration_gitama())
        assert self._specific_ref in heads or self._specific_ref in tags
        assert self._generic_ref and type(self._generic_ref) is str
        assert self._version and type(self._version) is str
        assert self._project in configuration.projects()


def main():
    AOSPEnvironment(Configuration.read_configuration(), '.', 'blah', 'android-8.1.0_r20', 'userdebug', 'sailfish',
                    'sailfish-7.1.1-int', 'generic-int', '4.0.0', 'falcon')


if __name__ == '__main__':
    main()
