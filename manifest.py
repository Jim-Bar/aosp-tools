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

import os
import sys
import tempfile
import xml.etree.ElementTree
import xmlindent

from commandline import LocalManifestCommandLineInterface
from configuration import Configuration
from sanity import SanityChecks
from typing import List, TextIO, Union


class LocalManifestRef(object):
    def __init__(self, name: str) -> None:
        self._name = name

    def name(self) -> str:
        return self._name


class LocalManifestRemote(object):
    def __init__(self, name: str, path: str) -> None:
        self._name = name
        self._path = path

    def name(self) -> str:
        return self._name

    def path(self) -> str:
        return self._path


class LocalManifestProject(object):
    def __init__(self, name: str) -> None:
        self._name = name

    def name(self) -> str:
        return self._name


class LocalManifestAddedProject(LocalManifestProject):
    def __init__(self, name: str, path: str, remote: LocalManifestRemote, groups: List[str], ref: LocalManifestRef,
                 children: List[xml.etree.ElementTree.Element]) -> None:
        super().__init__(name)
        self._children = children
        self._groups = groups
        self._path = path
        self._remote = remote
        self._ref = ref

    def children(self) -> List[xml.etree.ElementTree.Element]:
        return self._children

    def groups(self) -> List[str]:
        return self._groups

    def path(self) -> str:
        return self._path

    def ref(self) -> LocalManifestRef:
        return self._ref

    def remote(self) -> LocalManifestRemote:
        return self._remote

    def set_groups(self, new_groups: List[str]) -> None:
        self._groups = new_groups

    def set_path(self, new_path: str) -> None:
        self._path = new_path

    def set_ref(self, new_ref: LocalManifestRef) -> None:
        self._ref = new_ref

    def set_remote(self, new_remote: LocalManifestRemote) -> None:
        self._remote = new_remote


class LocalManifestRemovedProject(LocalManifestProject):
    """
    Sometimes removed projects' names do not match projects' paths (e.g. the project ``platform/build`` whose path is
    ``build/make``). Consequently it is sometimes impossible to associate a ``<remove-project>`` element with a
    ``<project>`` element. That is why removed paths cannot be stored as part of :class:`LocalManifestAddedProject` and
    need a separate entity, hence this class.

    For now a removed project is no more than a project containing an attribute ``name``, that is why this class adds
    nothing more to :class:`LocalManifestProject`.
    """
    pass


class LocalManifest(object):
    """
    Read a local manifest or template of local manifest from a file, from a repository or from a string. Then output it
    back to a file.
    """

    def __init__(self, projects: List[LocalManifestAddedProject], refs: List[LocalManifestRef],
                 remotes: List[LocalManifestRemote], removed_projects: List[LocalManifestRemovedProject]) -> None:
        self._projects = projects
        self._refs = refs
        self._remotes = remotes
        self._removed_projects = removed_projects

    @staticmethod
    def from_file(local_manifest_path: str) -> 'LocalManifest':
        with open(local_manifest_path) as local_manifest_file:
            return LocalManifest.from_string(local_manifest_file.read())

    @staticmethod
    def from_revisions(configuration: Configuration, generic_ref: str, ref: str, specific_ref: str) -> 'LocalManifest':
        with tempfile.TemporaryDirectory() as temp_directory:
            with configuration.repository_local_manifest().std_context(False, False):
                configuration.repository_local_manifest().clone(os.path.dirname(temp_directory),
                                                                os.path.basename(temp_directory))
                configuration.repository_local_manifest().checkout(ref)

            local_manifest_path = os.path.join(temp_directory, configuration.local_manifest_template_file())
            local_manifest_content = LocalManifest._customize_template_file(local_manifest_path, generic_ref,
                                                                            specific_ref)
            return LocalManifest.from_string(local_manifest_content)

    def projects(self) -> List[LocalManifestAddedProject]:
        return self._projects

    def refs(self) -> List[LocalManifestRef]:
        return self._refs

    def remotes(self) -> List[LocalManifestRemote]:
        return self._remotes

    def to_file(self, output_file: Union[str, TextIO]) -> None:
        manifest_node = xml.etree.ElementTree.Element('manifest')

        for remote in self._remotes:
            remote_element = xml.etree.ElementTree.Element('remote', {
                'name': remote.name(),
                'fetch': remote.path()
            })
            manifest_node.append(remote_element)

        for removed_project in self._removed_projects:
            remove_element = xml.etree.ElementTree.Element('remove-project', {
                'name': removed_project.name()
            })
            manifest_node.append(remove_element)

        for project in self._projects:
            project_element_attributes = {
                'name': project.name(),
                'path': project.path(),
                'remote': project.remote().name(),
                'revision': project.ref().name()
            }
            if project.groups():
                project_element_attributes['groups'] = ','.join(project.groups())
            project_element = xml.etree.ElementTree.Element('project', project_element_attributes)

            for child in project.children():
                project_element.append(child)

            manifest_node.append(project_element)

        xmlindent.indent(manifest_node)
        xml.etree.ElementTree.ElementTree(manifest_node).write(output_file, encoding='unicode', xml_declaration=True)

    @staticmethod
    def _customize_template_file(local_manifest_path: str, generic_ref: str, specific_ref: str) -> str:
        with open(local_manifest_path) as local_manifest_file:
            local_manifest_content = local_manifest_file.read()

        local_manifest_content = local_manifest_content.replace('@GENERIC@', generic_ref)
        local_manifest_content = local_manifest_content.replace('@SPECIFIC@', specific_ref)

        return local_manifest_content

    @staticmethod
    def from_string(local_manifest_content: str) -> 'LocalManifest':
        xml_root = xml.etree.ElementTree.fromstring(local_manifest_content)

        removed_projects = list()
        for xml_root_child in xml_root.findall('remove-project'):
            removed_projects.append(LocalManifestRemovedProject(xml_root_child.attrib['name']))

        refs = dict()

        remotes = dict()
        for xml_root_child in xml_root.findall('remote'):
            remote_name = xml_root_child.attrib['name']
            remote_path = xml_root_child.attrib['fetch']
            remotes[remote_name] = LocalManifestRemote(remote_name, remote_path)

        projects = list()
        for xml_root_child in xml_root.findall('project'):
            # Get name.
            name = xml_root_child.attrib['name']

            # Get path.
            path = xml_root_child.attrib['path']

            # Get remote.
            remote = remotes[xml_root_child.attrib['remote']]

            # Get groups.
            try:
                groups = xml_root_child.attrib['groups'].split(',')
            except KeyError:
                groups = list()

            # Get type (branch or tag) and revision name.
            ref_name = xml_root_child.attrib['revision'].split('/').pop()
            if ref_name not in refs:
                refs[ref_name] = LocalManifestRef(ref_name)
            ref = refs[ref_name]

            # Get children.
            children = list()
            for child in xml_root_child:
                children.append(child)

            projects.append(LocalManifestAddedProject(name, path, remote, groups, ref, children))

        return LocalManifest(projects, list(refs.values()), list(remotes.values()), removed_projects)


def main() -> None:
    SanityChecks.run()

    configuration = Configuration()
    cli = LocalManifestCommandLineInterface(configuration)
    local_manifest = LocalManifest.from_revisions(configuration, cli.generic_ref(), cli.ref(), cli.specific_ref())
    local_manifest.to_file(sys.stdout)


if __name__ == '__main__':
    main()
