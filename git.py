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

from typing import List, Tuple


class _GitUtils(object):
    """
    Various utility methods for Git.
    """

    @staticmethod
    def branch(working_directory: str) -> str:
        git_branch_command = ['git', 'branch']

        return subprocess.check_output(git_branch_command, cwd=working_directory).decode()

    @staticmethod
    def checkout(reference: str, working_directory: str) -> None:
        git_checkout_command = ['git', 'checkout', reference]
        subprocess.check_call(git_checkout_command, cwd=working_directory)

    @staticmethod
    def clone(working_directory: str, remote_url: str) -> None:
        git_clone_command = ['git', 'clone', remote_url]
        subprocess.check_call(git_clone_command, cwd=working_directory)

    @staticmethod
    def current_branch(working_directory: str) -> str:
        # Return the name of the current branch. If we are on a tag or particular commit, an exception is raised.
        git_symbolic_ref_command = ['git', 'symbolic-ref', 'HEAD']
        current_reference = subprocess.check_output(git_symbolic_ref_command, cwd=working_directory).decode()

        return current_reference.split('/').pop().strip()

    @staticmethod
    def current_commit(working_directory: str) -> str:
        # Return the hash of the current commit.
        git_rev_parse_command = ['git', 'rev-parse', 'HEAD']
        return subprocess.check_output(git_rev_parse_command, cwd=working_directory).decode().strip()

    @staticmethod
    def fetch(working_directory: str) -> None:
        git_fetch_command = ['git', 'fetch']
        subprocess.check_call(git_fetch_command, cwd=working_directory)

    @staticmethod
    def remote_refs(remote_url: str) -> Tuple[List[str], List[str]]:
        # Get the references from the repository (the repository is not cloned).
        git_ls_remote_command = ['git', 'ls-remote', remote_url]
        git_refs_raw = subprocess.check_output(git_ls_remote_command).splitlines()

        # Parse the output of 'git ls-remote' which is of the form:
        # '55ab6b26b5d037db88ce8f816829048c8de1f181\trefs/heads/sailfish-7.1.1-int'
        git_refs_raw = [git_ref.decode() for git_ref in git_refs_raw]
        git_refs_raw = [git_ref.split('/') for git_ref in git_refs_raw if '/heads/' in git_ref or '/tags/' in git_ref]
        git_heads = [git_head for _, git_type, git_head in git_refs_raw if git_type == 'heads']
        git_tags = [git_tag for _, git_type, git_tag in git_refs_raw if git_type == 'tags']

        return git_heads, git_tags

    @staticmethod
    def pull(working_directory: str) -> None:
        git_pull_command = ['git', 'pull']
        subprocess.check_call(git_pull_command, cwd=working_directory)

    @staticmethod
    def name(working_directory: str) -> str:
        # Return the name of the repository. The name is read based on the remote for push, so it may be incorrect.
        # If fetching the remote name fails (the repository does not have a remote, ...), an empty string is returned.
        git_remote_show_command = ['git', 'remote', 'show', '-n', 'origin']
        with open(os.devnull, 'w') as devnull:
            try:
                git_remote_data = subprocess.check_output(git_remote_show_command, cwd=working_directory,
                                                          stderr=devnull).decode().splitlines()
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
    def status(working_directory: str) -> List[str]:
        git_status_command = ['git', 'status', '-s']
        return subprocess.check_output(git_status_command, cwd=working_directory).decode().split()


class Repository(object):
    """
    A repository is just a path and a name.
    """

    def __init__(self, protocol: str, user: str, remote: str, path: str, name: str) -> None:
        self._protocol = protocol
        self._user = user
        self._remote = remote
        self._path = path
        self._name = name

    def _get_remote_url(self) -> str:
        if self._protocol == 'file':
            return 'file://{}/{}/{}'.format(self._remote, self._path, self._name)
        elif self._protocol == 'ssh':
            return '{}@{}:{}/{}'.format(self._user, self._remote, self._path, self._name)
        elif self._protocol == 'http':
            return 'http://{}/{}/{}'.format(self._remote, self._path, self._name)
        elif self._protocol == 'https':
            return 'https://{}/{}/{}'.format(self._remote, self._path, self._name)

    def remote_refs(self) -> Tuple[List[str], List[str]]:
        return _GitUtils.remote_refs(self._get_remote_url())
