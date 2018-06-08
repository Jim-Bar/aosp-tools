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
import sys
import tempfile
import xml.etree.ElementTree
import xmlindent

from commandline import LocalManifestCommandLineInterface
from configuration import Configuration
from typing import List, TextIO, Union


class LocalManifestRef(object):
    def __init__(self, name: str, is_tag: bool) -> None:
        self._name = name
        self._is_tag = is_tag

    def is_tag(self) -> bool:
        return self._is_tag

    def name(self) -> str:
        return self._name

    def type(self) -> str:
        return 'tag' if self._is_tag else 'head'


class LocalManifestRemote(object):
    def __init__(self, name: str, path: str) -> None:
        self._name = name
        self._path = path

    def name(self) -> str:
        return self._name

    def path(self) -> str:
        return self._path


class LocalManifestProject(object):
    def __init__(self, name: str, path: str, remote: LocalManifestRemote, groups: List[str], ref: LocalManifestRef,
                 override: bool, children: List[xml.etree.ElementTree.Element]) -> None:
        self._children = children
        self._groups = groups
        self._name = name
        self._override = override
        self._path = path
        self._remote = remote
        self._ref = ref

    def children(self) -> List[xml.etree.ElementTree.Element]:
        return self._children

    def groups(self) -> List[str]:
        return self._groups

    def name(self) -> str:
        return self._name

    def override(self) -> bool:
        return self._override

    def path(self) -> str:
        return self._path

    def ref(self) -> LocalManifestRef:
        return self._ref

    def remote(self) -> LocalManifestRemote:
        return self._remote

    def set_groups(self, new_groups: List[str]) -> None:
        self._groups = new_groups

    def set_override(self, new_override: bool) -> None:
        self._override = new_override

    def set_path(self, new_path: str) -> None:
        self._path = new_path

    def set_ref(self, new_ref: LocalManifestRef) -> None:
        self._ref = new_ref

    def set_remote(self, new_remote: LocalManifestRemote) -> None:
        self._remote = new_remote


class LocalManifest(object):

    def __init__(self, projects: List[LocalManifestProject], refs: List[LocalManifestRef],
                 remotes: List[LocalManifestRemote]) -> None:
        self._projects = projects
        self._refs = refs
        self._remotes = remotes

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

            ref_is_tag = specific_ref in configuration.repository_local_manifest().get_tags()

            local_manifest_path = os.path.join(temp_directory, configuration.local_manifest_file())
            local_manifest_content = LocalManifest._customize_template_file(ref_is_tag, local_manifest_path,
                                                                            generic_ref, specific_ref)
            return LocalManifest.from_string(local_manifest_content)

    def projects(self) -> List[LocalManifestProject]:
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
                'fetch': remote.path(),
                'alias': 'origin'
            })
            manifest_node.append(remote_element)

        for project in self._projects:
            if project.override():
                remove_element = xml.etree.ElementTree.Element('remove-project', {
                    'name': '{}{}'.format('' if project.path().startswith('device/') else 'platform/', project.path())
                })
                manifest_node.append(remove_element)

            project_element_attributes = {
                'clone-depth': '{}'.format(1),
                'name': project.name(),
                'path': project.path(),
                'remote': project.remote().name(),
                'revision': 'refs/{}s/{}'.format(project.ref().type(), project.ref().name())
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
    def _customize_template_file(ref_is_tag: bool, local_manifest_path: str, generic_ref: str,
                                 specific_ref: str) -> str:
        with open(local_manifest_path) as local_manifest_file:
            local_manifest_content = local_manifest_file.read()

        local_manifest_content = local_manifest_content.replace('@TYPE@', 'tags' if ref_is_tag else 'heads')
        local_manifest_content = local_manifest_content.replace('@GENERIC_VERSION@', generic_ref)
        local_manifest_content = local_manifest_content.replace('@SPECIFIC_VERSION@', specific_ref)

        return local_manifest_content

    @staticmethod
    def from_string(local_manifest_content: str) -> 'LocalManifest':
        xml_root = xml.etree.ElementTree.fromstring(local_manifest_content)

        removed_paths = list()
        for xml_root_child in xml_root.findall('remove-project'):
            path = xml_root_child.attrib['name']

            # The path may be prefixed by a component which is not actually part of the path. Remove it.
            platform_prefix = 'platform/'
            if path.startswith(platform_prefix):
                path = path[len(platform_prefix):]

            removed_paths.append(path)

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
            _, ref_type, ref_name = xml_root_child.attrib['revision'].split('/')
            if ref_name not in refs:
                refs[ref_name] = LocalManifestRef(ref_name, ref_type == 'tags')
            ref = refs[ref_name]

            # If the path of the repository is in the list of the removed projects' paths, this means that this
            # repository overrides another repository. Mark it as such.
            overrides = xml_root_child.attrib['path'] in removed_paths

            # Get children.
            children = list()
            for child in xml_root_child:
                children.append(child)

            projects.append(LocalManifestProject(name, path, remote, groups, ref, overrides, children))

        return LocalManifest(projects, list(refs.values()), list(remotes.values()))


def main():
    configuration = Configuration.read_configuration()
    cli = LocalManifestCommandLineInterface(configuration)
    local_manifest = LocalManifest.from_revisions(configuration, cli.generic_ref(), cli.ref(), cli.specific_ref())
    local_manifest.to_file(sys.stdout)


if __name__ == '__main__':
    main()
