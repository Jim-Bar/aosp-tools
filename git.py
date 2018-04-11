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

# This import can be safely ignored if it fails. Those items are used for type hints (PEP 484) in comments.
# Refer to: https://www.python.org/dev/peps/pep-0484/
# Also useful: http://mypy.readthedocs.io/en/latest/cheat_sheet.html
try:
    from typing import Dict, List, Any, Tuple, Union
except ImportError:
    Dict, List, Any, Tuple, Union = None, None, None, None, None


class GitConfiguration(object):
    """
    Holds data on a Git configuration: user, server, ...
    """

    def __init__(self, user, server, protocol):
        # type: (Union[str, None], str, str) -> None

        self._user = user  # type: str
        self._server = server  # type: str
        self._protocol = protocol  # type: str

    def get_url(self, repository_path, repository_name):
        # type: (str, str) -> str

        if self._protocol == 'file':
            return 'file://{}/{}/{}'.format(self.server(), repository_path, repository_name)
        elif self._protocol == 'ssh':
            return '{}@{}:{}/{}'.format(self.user(), self.server(), repository_path, repository_name)
        elif self._protocol == 'http':
            return 'http://{}/{}/{}'.format(self.server(), repository_path, repository_name)
        elif self._protocol == 'https':
            return 'https://{}/{}/{}'.format(self.server(), repository_path, repository_name)

    def server(self):
        # type: () -> str

        return self._server

    def user(self):
        # type: () -> str

        return self._user


class GitUtils(object):
    """
    Various utility methods for Git.
    """

    @staticmethod
    def branch(working_directory):
        # type: (str) -> str

        git_branch_command = ['git', 'branch']

        return subprocess.check_output(git_branch_command, cwd=working_directory).decode()

    @staticmethod
    def checkout(reference, working_directory):
        # type: (str, str) -> None

        git_checkout_command = ['git', 'checkout', reference]
        subprocess.check_call(git_checkout_command, cwd=working_directory)

    @staticmethod
    def clone(repository_name, repository_path, working_directory, git_configuration):
        # type: (str, str, str, GitConfiguration) -> None

        git_clone_command = ['git', 'clone', git_configuration.get_url(repository_name, repository_path)]
        subprocess.check_call(git_clone_command, cwd=working_directory)

    @staticmethod
    def current_branch(working_directory):
        # type: (str) -> str

        # Return the name of the current branch. If we are on a tag or particular commit, an exception is raised.
        git_symbolic_ref_command = ['git', 'symbolic-ref', 'HEAD']
        current_reference = subprocess.check_output(git_symbolic_ref_command, cwd=working_directory).decode()

        return current_reference.split('/').pop().strip()

    @staticmethod
    def current_commit(working_directory):
        # type: (str) -> str

        # Return the hash of the current commit.
        git_rev_parse_command = ['git', 'rev-parse', 'HEAD']
        return subprocess.check_output(git_rev_parse_command, cwd=working_directory).decode().strip()

    @staticmethod
    def fetch(working_directory):
        # type: (str) -> None

        git_fetch_command = ['git', 'fetch']
        subprocess.check_call(git_fetch_command, cwd=working_directory)

    @staticmethod
    def remote_refs(repository_name, repository_path, git_configuration):
        # type: (str, str, GitConfiguration) -> Tuple[List[str], List[str]]

        # Get the references from the repository (the repository is not cloned).
        git_ls_remote_command = ['git', 'ls-remote', git_configuration.get_url(repository_name, repository_path)]
        git_refs_raw = subprocess.check_output(git_ls_remote_command).splitlines()

        # Parse the output of 'git ls-remote' which is of the form:
        # '55ab6b26b5d037db88ce8f816829048c8de1f181\trefs/heads/sailfish-7.1.1-int'
        git_refs_raw = [git_ref.decode() for git_ref in git_refs_raw]
        git_refs_raw = [git_ref.split('/') for git_ref in git_refs_raw if '/heads/' in git_ref or '/tags/' in git_ref]
        git_heads = [git_head for _, git_type, git_head in git_refs_raw if git_type == 'heads']
        git_tags = [git_tag for _, git_type, git_tag in git_refs_raw if git_type == 'tags']

        return git_heads, git_tags

    @staticmethod
    def pull(working_directory):
        # type: (str) -> None

        git_pull_command = ['git', 'pull']
        subprocess.check_call(git_pull_command, cwd=working_directory)

    @staticmethod
    def name(working_directory):
        # type: (str) -> str

        # Return the name of the repository. The name is read based on the remote for push, so it may be incorrect.
        # If fetching the remote name fails (the repository does not have a remote, ...), an empty string is returned.
        git_remote_show_command = ['git', 'remote', 'show', '-n', 'origin']
        with open(os.devnull, 'w') as devnull:
            try:
                git_remote_data = subprocess.check_output(git_remote_show_command, cwd=working_directory,
                                                          stderr=devnull).decode('utf-8').splitlines()
            except subprocess.CalledProcessError:
                # This is probably not a repository. In all cases, the name cannot be found, so return an empty string.
                return ''

        # Parse the remote data to extract the name of the repository.
        git_remote = ''
        for git_remote_data_piece in git_remote_data:
            if 'push' in git_remote_data_piece.lower() and 'url' in git_remote_data_piece.lower():
                git_remote = git_remote_data_piece.split().pop().split(':').pop().split('/').pop()
                break

        # If the name is 'origin' that is most likely because the repository does not have a remote. Or the repository
        # is called 'origin', but here we will admit that it is not the case, too bad.
        if git_remote == 'origin':
            return ''

        return git_remote

    @staticmethod
    def status(working_directory):
        # type: (str) -> List[str]

        git_status_command = ['git', 'status', '-s']
        return subprocess.check_output(git_status_command, cwd=working_directory)


class Repository(object):
    """
    A repository is just a path and a name.
    """

    def __init__(self, path, name):
        self._path = path
        self._name = name

    def path(self):
        return self._path

    def name(self):
        return self._name
