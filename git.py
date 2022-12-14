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

import contextlib
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
    def checkout(reference: str, working_directory: str, stderr: bool=True, stdout: bool=True) -> None:
        git_checkout_command = ['git', 'checkout', reference]
        subprocess.check_call(git_checkout_command, cwd=working_directory, stderr=_GitUtils._std(stderr),
                              stdout=_GitUtils._std(stdout))

    @staticmethod
    def clone(working_directory: str, remote_url: str, directory_name: str='', stderr: bool=True,
              stdout: bool=False) -> None:
        git_clone_command = ['git', 'clone', remote_url]
        if directory_name:
            git_clone_command.append(directory_name)
        subprocess.check_call(git_clone_command, cwd=working_directory, stderr=_GitUtils._std(stderr),
                              stdout=_GitUtils._std(stdout))

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
    def fetch(working_directory: str, stderr: bool=True, stdout: bool=True) -> None:
        git_fetch_command = ['git', 'fetch']
        subprocess.check_call(git_fetch_command, cwd=working_directory, stderr=_GitUtils._std(stderr),
                              stdout=_GitUtils._std(stdout))

    @staticmethod
    def get_branches(working_directory: str) -> Tuple[List[str], List[str]]:
        # Local branches.
        git_branches_command = ['git', 'for-each-ref', 'refs/heads']
        local_branches = subprocess.check_output(git_branches_command, cwd=working_directory).decode().splitlines()
        local_branches = [item.split()[2].split('/')[-1] for item in local_branches]

        # Remote branches.
        git_branches_command = ['git', 'for-each-ref', 'refs/remotes']
        remote_branches = subprocess.check_output(git_branches_command, cwd=working_directory).decode().splitlines()
        remote_branches = [item.split()[2].split('/')[-1] for item in remote_branches]

        return local_branches, remote_branches

    @staticmethod
    def get_tags(working_directory: str) -> List[str]:
        git_tags_command = ['git', 'for-each-ref', 'refs/tags']
        tags = subprocess.check_output(git_tags_command, cwd=working_directory).decode().splitlines()
        tags = [item.split()[2].split('/')[-1] for item in tags]

        return tags

    @staticmethod
    def remote_refs(remote_url: str) -> Tuple[List[str], List[str]]:
        # Get the references from the repository (the repository is not cloned).
        git_ls_remote_command = ['git', 'ls-remote', remote_url]
        git_refs_raw = subprocess.check_output(git_ls_remote_command).splitlines()

        # Parse the output of 'git ls-remote' which is of the form:
        # '55ab6b26b5d037db88ce8f816829048c8de1f181\trefs/heads/sailfish-7.1.1-int'
        git_refs_raw = [git_ref.decode() for git_ref in git_refs_raw]
        git_refs_raw = [git_ref.split('/', 2) for git_ref in git_refs_raw
                        if '/heads/' in git_ref or '/tags/' in git_ref]
        git_heads = [git_head for _, git_type, git_head in git_refs_raw if git_type == 'heads']
        git_tags = [git_tag for _, git_type, git_tag in git_refs_raw if git_type == 'tags']

        return git_heads, git_tags

    @staticmethod
    def pull(working_directory: str, stderr: bool=True, stdout: bool=True) -> None:
        git_pull_command = ['git', 'pull']
        subprocess.check_call(git_pull_command, cwd=working_directory, stderr=_GitUtils._std(stderr),
                              stdout=_GitUtils._std(stdout))

    @staticmethod
    def name(working_directory: str) -> str:
        # Return the name of the repository. The name is read based on the remote for push, so it may be incorrect.
        # If fetching the remote name fails (the repository does not have a remote, ...), an empty string is returned.
        git_remote_show_command = ['git', 'remote', 'show', '-n', 'origin']

        try:
            git_remote_data = subprocess.check_output(git_remote_show_command,
                                                      cwd=working_directory).decode().splitlines()
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

    @staticmethod
    def _std(is_enabled: bool):
        return None if is_enabled else subprocess.DEVNULL


class Repository(object):
    """
    A repository is just a path and a name.
    """

    def __init__(self, protocol: str, user: str, remote: str, path: str, name: str) -> None:
        self._clone_path = ''
        self._protocol = protocol
        self._user = user
        self._remote = remote
        self._path = path
        self._name = name
        self._stderr_enabled = True
        self._stdout_enabled = True

    def checkout(self, ref: str) -> None:
        self._check_cloned()

        _GitUtils.checkout(ref, self._clone_path, stderr=self._stderr_enabled, stdout=self._stdout_enabled)

    def clone(self, working_directory: str, directory_name: str='') -> None:
        _GitUtils.clone(working_directory, self.get_remote_url(), directory_name, stderr=self._stderr_enabled,
                        stdout=self._stdout_enabled)
        self._clone_path = os.path.realpath(os.path.join(working_directory, directory_name))

    def get_branches(self) -> Tuple[List[str], List[str]]:
        self._check_cloned()

        return _GitUtils.get_branches(self._clone_path)

    def get_path_name(self) -> str:
        return '{}/{}'.format(self._path, self._name)

    def get_tags(self) -> List[str]:
        self._check_cloned()

        return _GitUtils.get_tags(self._clone_path)

    def get_remote_url(self) -> str:
        if self._protocol == 'file':
            return 'file://{}/{}'.format(self._remote, self.get_path_name())
        elif self._protocol == 'ssh':
            return '{}@{}:{}'.format(self._user, self._remote, self.get_path_name())
        elif self._protocol == 'http':
            return 'http://{}/{}'.format(self._remote, self.get_path_name())
        elif self._protocol == 'https':
            return 'https://{}/{}'.format(self._remote, self.get_path_name())

    def remote_refs(self) -> Tuple[List[str], List[str]]:
        return _GitUtils.remote_refs(self.get_remote_url())

    @contextlib.contextmanager
    def std_context(self, stderr_enabled: bool, stdout_enabled: bool):
        stderr_enabled_initial = self._stderr_enabled
        stdout_enabled_initial = self._stdout_enabled
        self._stderr_enabled = stderr_enabled
        self._stdout_enabled = stdout_enabled
        yield
        self._stderr_enabled = stderr_enabled_initial
        self._stdout_enabled = stdout_enabled_initial

    def _check_cloned(self) -> None:
        if not self._clone_path:
            raise EnvironmentError('The repository {} is not cloned'.format(self.get_remote_url()))
