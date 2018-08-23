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
import sys
import xml.etree.ElementTree

from commandline import AOSPTreeCommandLineInterface
from configuration import Configuration
from manifest import LocalManifest
from repo import RepoAdapter
from sanity import SanityChecks


class AOSPTree(object):
    """
    An :class:`AOSPTree` basically is the path to an AOSP source tree for a given release of Android. Note that it only
    represents the source files, and not the built files. It can be fed to a :class:`aospbuild.AOSPBuild` for actually
    building the sources.
    """

    def __init__(self, configuration: Configuration, path: str) -> None:
        path = os.path.abspath(path)
        if not os.path.isfile(os.path.join(path, configuration.source_env_file_path())):
            raise EnvironmentError('Not an AOSP tree: "{}"'.format(path))

        self._path = path
        with contexts.set_cwd(path):
            self._revision = AOSPTree._find_revision()

    def __str__(self) -> str:
        return AOSPTree.description(self.path(), self.revision())

    @staticmethod
    def clone(configuration: Configuration, path: str, revision: str,
              local_manifest: LocalManifest, num_cores: int) -> 'AOSPTree':
        os.mkdir(path)

        with contexts.set_cwd(path):
            with contexts.set_variable('REPO_TRACE', str(1 if configuration.repo_trace() else 0)):
                # Repo init.
                RepoAdapter.init(configuration.repository_manifest().get_remote_url(), revision,
                                 configuration.repo_groups(), configuration.repo_depth())

                # Fetch local manifest.
                local_manifest_path = os.path.join(RepoAdapter.INSTALL_DIRECTORY,
                                                   configuration.local_manifest_directory())
                os.mkdir(local_manifest_path)
                local_manifest.to_file(os.path.join(local_manifest_path, configuration.local_manifest_file()))

                # Repo sync.
                RepoAdapter.sync(num_cores, configuration.repo_only_current_branch(), configuration.repo_no_tags())

                return AOSPTree(configuration, path)

    @staticmethod
    def description(path: str, revision: str) -> str:
        description = list()
        description.append('Path: {}'.format(path))
        description.append('Release: {}'.format(revision))
        description.append('-' * max(map(len, description)))
        description.insert(0, description[-1])

        return '\n'.join(description)

    def path(self) -> str:
        return self._path

    def revision(self) -> str:
        return self._revision

    @staticmethod
    def _find_revision() -> str:
        xml_root = xml.etree.ElementTree.fromstring(RepoAdapter.manifest())
        return xml_root.findall('default').pop().attrib['revision'].split('/').pop()


def main() -> None:
    SanityChecks.run()

    configuration = Configuration()
    cli = AOSPTreeCommandLineInterface(configuration)
    print(AOSPTree.description(cli.path(), cli.release()))
    if cli.press_enter():
        AOSPTree.clone(configuration, cli.path(), cli.release(), LocalManifest.from_string(cli.local_manifest()),
                       cli.num_cores())
    else:
        sys.exit(os.EX_USAGE)  # Set an error code for canceling chained commands.


if __name__ == '__main__':
    main()
