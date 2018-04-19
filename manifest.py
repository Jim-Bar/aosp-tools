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
import tempfile
import xml.etree.ElementTree
import xmlindent

from configuration import Configuration
from typing import List


class _LocalManifestRemote(object):
    def __init__(self, name: str, path: str) -> None:
        self._name = name
        self._path = path

    def name(self) -> str:
        return self._name

    def path(self) -> str:
        return self._path


class _LocalManifestProject(object):
    def __init__(self, name: str, path: str, remote: _LocalManifestRemote, groups: str, ref_type: str, ref_name: str,
                 override: bool, children: List[xml.etree.ElementTree.Element]) -> None:
        self._children = children
        self._groups = groups
        self._name = name
        self._override = override
        self._path = path
        self._remote = remote
        self._ref_name = ref_name
        self._ref_type = ref_type

    def children(self) -> List[xml.etree.ElementTree.Element]:
        return self._children

    def groups(self) -> str:
        return self._groups

    def name(self) -> str:
        return self._name

    def override(self) -> bool:
        return self._override

    def path(self) -> str:
        return self._path

    def remote(self) -> _LocalManifestRemote:
        return self._remote

    def ref_name(self) -> str:
        return self._ref_name

    def ref_type(self) -> str:
        return self._ref_type


class LocalManifest(object):

    def __init__(self, projects: List[_LocalManifestProject], remotes: List[_LocalManifestRemote]) -> None:
        self._projects = projects
        self._remotes = remotes

    @staticmethod
    def from_file(local_manifest_path: str) -> 'LocalManifest':
        with open(local_manifest_path) as local_manifest_file:
            return LocalManifest._from_string(local_manifest_file.read())

    @staticmethod
    def from_revisions(configuration: Configuration, generic_ref: str, specific_ref: str) -> 'LocalManifest':
        with tempfile.TemporaryDirectory() as temp_directory:
            configuration.repository_local_manifest().clone(os.path.dirname(temp_directory),
                                                            os.path.basename(temp_directory))
            configuration.repository_local_manifest().checkout(specific_ref)

            if specific_ref in configuration.repository_local_manifest().get_tags():
                ref_type = 'tags'
            else:
                ref_type = 'heads'

            local_manifest_path = os.path.join(temp_directory, configuration.local_manifest_file())
            local_manifest_content = LocalManifest._customize_template_file(ref_type, local_manifest_path, generic_ref,
                                                                            specific_ref)
            return LocalManifest._from_string(local_manifest_content)

    def to_file(self, file_path: str) -> None:
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
                'revision': 'refs/{}/{}'.format(project.ref_type(), project.ref_name())
            }
            if project.groups():
                project_element_attributes['groups'] = project.groups()
            project_element = xml.etree.ElementTree.Element('project', project_element_attributes)

            for child in project.children():
                project_element.append(child)

            manifest_node.append(project_element)

        xmlindent.indent(manifest_node)
        xml.etree.ElementTree.ElementTree(manifest_node).write(file_path, encoding='UTF-8', xml_declaration=True)

    @staticmethod
    def _customize_template_file(ref_type: str, local_manifest_path: str, generic_ref: str, specific_ref: str) -> str:
        with open(local_manifest_path) as local_manifest_file:
            local_manifest_content = local_manifest_file.read()

        local_manifest_content = local_manifest_content.replace('@TYPE@', ref_type)
        local_manifest_content = local_manifest_content.replace('@GENERIC_VERSION@', generic_ref)
        local_manifest_content = local_manifest_content.replace('@SPECIFIC_VERSION@', specific_ref)

        return local_manifest_content

    @staticmethod
    def _from_string(local_manifest_content: str) -> 'LocalManifest':
        xml_root = xml.etree.ElementTree.fromstring(local_manifest_content)

        removed_paths = list()
        for xml_root_child in xml_root.findall('remove-project'):
            path = xml_root_child.attrib['name']

            # The path may be prefixed by a component which is not actually part of the path. Remove it.
            platform_prefix = 'platform/'
            if path.startswith(platform_prefix):
                path = path[len(platform_prefix):]

            removed_paths.append(path)

        remotes = dict()
        for xml_root_child in xml_root.findall('remote'):
            remote_name = xml_root_child.attrib['name']
            remote_path = xml_root_child.attrib['fetch']
            remotes[remote_name] = _LocalManifestRemote(remote_name, remote_path)

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
                groups = xml_root_child.attrib['groups']
            except KeyError:
                groups = ''

            # Get type (branch or tag) and revision name.
            _, ref_type, ref_name = xml_root_child.attrib['revision'].split('/')

            # If the path of the repository is in the list of the removed projects' paths, this means that this
            # repository overrides another repository. Mark it as such.
            overrides = xml_root_child.attrib['path'] in removed_paths

            # Get children.
            children = list()
            for child in xml_root_child:
                children.append(child)

            projects.append(_LocalManifestProject(name, path, remote, groups, ref_type, ref_name, overrides, children))

        return LocalManifest(projects, list(remotes.values()))
