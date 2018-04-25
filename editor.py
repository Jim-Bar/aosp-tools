# TODO: hashbang to virtualenv.
# -*- coding:utf8  -*-

#
# AMA SA CONFIDENTIAL
# __________________
#
#  [2014] - [2018] AMA SA Incorporated
#  All Rights Reserved.
#
# NOTICE:  All information contained herein is, and remains
# the property of AMA SA Systems Incorporated and its suppliers,
# if any.  The intellectual and technical concepts contained
# herein are proprietary to AMA SA Incorporated
# and its suppliers and may be covered by E.U. and Foreign Patents,
# patents in process, and are protected by trade secret or copyright law.
# Dissemination of this information or reproduction of this material
# is strictly forbidden unless prior written permission is obtained
# from AMA SA Incorporated.
#
# The above copyright notice and this permission notice must be included
# in all copies of this file.
#

import configuration
import manifest
import urwid

from typing import List, Tuple


class _ManifestEditorPanelCategory(urwid.Pile):
    """
    TODO
    """

    def __init__(self, category_name: str, items: List[Tuple[str, int]]) -> None:
        remotes_title_widget = urwid.Text(category_name)

        remotes_divider_widget = urwid.Divider()
        remote_widgets = urwid.Pile([])
        for content in items:
            remote_widgets.contents.append((_ManifestEditorPanelCategory._create_content_widget(*content),
                                            remote_widgets.options('pack', None)))

        super().__init__([
            remotes_title_widget,
            remotes_divider_widget,
            remote_widgets
        ])

    @staticmethod
    def _create_content_widget(content: str, count: int) -> urwid.Columns:
        remote_content_widget = urwid.SelectableIcon(content, cursor_position=0)
        remote_count_widget = urwid.Text('[{}]'.format(count), align='right')
        return urwid.Columns([
            ('weight', 26, remote_content_widget),
            ('weight', 3, remote_count_widget)
        ])


class _ManifestEditorPanel(urwid.Pile):
    """
    TODO
    """

    _INFO = '(Action: SPACE, Edit: e, Add: +, Remove: -)'

    def __init__(self, projects: List[manifest.LocalManifestProject], remotes: List[manifest.LocalManifestRemote],
                 revisions: List[manifest.LocalManifestRef]) -> None:
        groups = set()
        for project in projects:
            groups.update(project.groups())

        groups = [(group, 0) for group in groups]
        remotes = [('{} -> {}'.format(remote.name(), remote.path()), 0) for remote in remotes]
        revisions = [('{}/{}'.format(revision.name(), revision.type()), 0) for revision in revisions]

        super().__init__([
            _ManifestEditorPanelCategory('Remotes', remotes),
            _ManifestEditorPanelCategory('Revisions', revisions),
            _ManifestEditorPanelCategory('Groups', groups),
            urwid.Text(_ManifestEditorPanel._INFO)
        ])


class _ManifestEditorProjectList(urwid.Pile):
    """
    TODO
    """

    def __init__(self, projects: List[manifest.LocalManifestProject]) -> None:
        max_name = len(max(projects, key=lambda item: len(item.name())).name())
        max_path = len(max(projects, key=lambda item: len(item.path())).path())
        max_revision = len(max(projects, key=lambda item: len(item.ref().name())).ref().name())
        max_remote = len(max(projects, key=lambda item: len(item.remote().name())).remote().name())
        max_groups = len(','.join(max(projects, key=lambda item: len(','.join(item.groups()))).groups()))

        max_name = max(max_name, len('name'))
        max_path = max(max_path, len('path'))
        max_revision = max(max_revision, len('revision'))
        max_remote = max(max_remote, len('remote'))
        max_groups = max(max_groups, len('groups'))

        project_widgets = list()
        for project in projects:
            project_widgets.append(_ManifestEditorProjectList._create_project_widget(
                project.name(), max_name, project.path(), max_path, project.override(), project.ref().name(),
                max_revision, project.remote().name(), max_remote, project.groups(), max_groups))

        super().__init__([
            urwid.Text('  {} {} {} {} {}'.format('name'.ljust(max_name, ' '), 'path'.ljust(max_path, ' '),
                                                 'revision'.ljust(max_revision, ' '), 'remote'.ljust(max_remote, ' '),
                                                 'groups'.ljust(max_groups, ' '))),
            urwid.Pile(project_widgets)
        ])

    @staticmethod
    def _create_project_widget(name: str, name_len: int, path: str, path_len: int, override: bool, revision: str,
                               revision_len: int, remote: str, remote_len: int, groups: List[str],
                               groups_len: int) -> urwid.SelectableIcon:
        return urwid.SelectableIcon('{} {} {} {} {} {}'
                                    .format('*' if override else ' ', name.ljust(name_len, ' '), path.ljust(path_len),
                                            revision.ljust(revision_len), remote.ljust(remote_len),
                                            ','.join(groups).ljust(groups_len)),
                                    cursor_position=0)


class ManifestEditor(object):
    """
    TODO
    """

    def __init__(self, local_manifest: manifest.LocalManifest) -> None:
        projects = urwid.Filler(_ManifestEditorProjectList(local_manifest.projects()), 'top')
        panel = urwid.Filler(_ManifestEditorPanel(local_manifest.projects(), local_manifest.remotes(),
                                                  local_manifest.refs()), 'top')
        urwid.MainLoop(urwid.Columns([projects, (50, panel)])).run()


if __name__ == '__main__':
    ManifestEditor(manifest.LocalManifest.from_revisions(configuration.Configuration.read_configuration(),
                                                         'generic-int', 'sailfish-7.1.1-int'))
