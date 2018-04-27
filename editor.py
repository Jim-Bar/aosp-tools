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

from typing import Callable, Iterable, List, Set, Tuple, Union


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
                                            remote_widgets.options(urwid.PACK, None)))

        super().__init__([
            remotes_title_widget,
            remotes_divider_widget,
            remote_widgets
        ])

    def columns(self) -> int:
        required_widths = [len(widget.contents[0][0].text) + len(widget.contents[1][0].text) + 2
                           for widget, _ in self.contents[-1][0].contents]
        return max(required_widths)

    @staticmethod
    def _create_content_widget(content: str, count: int) -> urwid.Columns:
        remote_content_widget = urwid.SelectableIcon(content, cursor_position=0)
        remote_count_widget = urwid.Text('[{}]'.format(count), align=urwid.RIGHT)
        return urwid.Columns([
            (urwid.WEIGHT, 26, remote_content_widget),
            (urwid.WEIGHT, 3, remote_count_widget)
        ])


class _ManifestEditorPanel(urwid.Pile):
    """
    TODO
    """

    _INFO = '(Action: SPACE, Edit: e, Add: +, Remove: -)'

    def __init__(self, groups: Set[str], remotes: List[Tuple[str, str]], revisions: List[Tuple[str, str]]) -> None:
        groups = [(group, 0) for group in groups]
        remotes = [('{} -> {}'.format(name, path), 0) for name, path in remotes]
        revisions = [('{}/{}'.format(name, type_name), 0) for name, type_name in revisions]

        super().__init__([
            _ManifestEditorPanelCategory('Remotes', remotes),
            _ManifestEditorPanelCategory('Revisions', revisions),
            _ManifestEditorPanelCategory('Groups', groups),
            urwid.Text(_ManifestEditorPanel._INFO)
        ])

    def columns(self) -> int:
        required_widths = [category.columns() for category, _ in self.contents
                           if type(category) is _ManifestEditorPanelCategory]
        return max(required_widths)


class _ManifestEditorProjectList(urwid.Pile):
    """
    TODO
    """

    def __init__(self, projects: List[Tuple[str, str, bool, str, str, List[str]]]) -> None:
        self._projects = dict()

        self._max_name = _ManifestEditorProjectList._max_length(projects, 0, 'name')
        self._max_path = _ManifestEditorProjectList._max_length(projects, 1, 'path')
        self._max_revision = _ManifestEditorProjectList._max_length(projects, 3, 'revision')
        self._max_remote = _ManifestEditorProjectList._max_length(projects, 4, 'remote')
        self._max_groups = _ManifestEditorProjectList._max_length(projects, 5, 'groups', ','.join)

        for name, path, override, revision, remote, groups in projects:
            self._projects[name] = self._create_project_widget(name, path, override, revision, remote, groups)

        super().__init__([
            urwid.Text('  {} {} {} {} {}'.format('name'.ljust(self._max_name, ' '), 'path'.ljust(self._max_path, ' '),
                                                 'revision'.ljust(self._max_revision, ' '),
                                                 'remote'.ljust(self._max_remote, ' '),
                                                 'groups'.ljust(self._max_groups, ' '))),
            urwid.Pile(self._projects.values())
        ])

    def _create_project_widget(self, name: str, path: str, override: bool, revision: str, remote: str,
                               groups: List[str]) -> urwid.SelectableIcon:
        return urwid.SelectableIcon('{} {} {} {} {} {}'
                                    .format('*' if override else ' ', name.ljust(self._max_name, ' '),
                                            path.ljust(self._max_path), revision.ljust(self._max_revision),
                                            remote.ljust(self._max_remote), ','.join(groups).ljust(self._max_groups)),
                                    cursor_position=0)

    @staticmethod
    def _max_length(projects: List[Tuple[str, str, bool, str, str, List[str]]], index: int, caption: str,
                    func: Callable[[Iterable[str]], str]=lambda x: x) -> int:
        return max(max(map(lambda item: len(func(item[index])), projects)), len(caption))


class _GUI(object):
    """
    TODO
    """

    def __init__(self, projects: List[Tuple[str, str, bool, str, str, List[str]]], remotes: List[Tuple[str, str]],
                 revisions: List[Tuple[str, str]]) -> None:
        projects_widget = _ManifestEditorProjectList(projects)
        groups = set()
        for project in projects:
            groups.update(project[-1])
        panel = _ManifestEditorPanel(groups, revisions, remotes)
        urwid.MainLoop(urwid.Columns([
            urwid.Filler(projects_widget, urwid.TOP),
            (panel.columns(), urwid.Filler(panel, urwid.TOP))
        ])).run()


class ManifestEditor(object):
    """
    Link between the local manifest object and urwid.
    """

    def __init__(self, local_manifest: manifest.LocalManifest) -> None:
        projects = [(project.name(), project.path(), project.override(), project.ref().name(), project.remote().name(),
                     project.groups()) for project in local_manifest.projects()]
        _GUI(projects, [(remote.name(), remote.path()) for remote in local_manifest.remotes()],
             [(ref.name(), ref.type()) for ref in local_manifest.refs()])

    def on_group_added(self, group_name: str) -> None:
        pass

    def on_group_renamed(self, group_old_name: str, group_new_name: str) -> None:
        pass

    def on_group_removed(self, group_name: str) -> None:
        pass

    def on_project_added(self, project_name: str, project_path: str, override: bool) -> None:
        pass

    def on_project_edited(self, project_name: str, project_path: str='', remote_name: str='', revision_name: str='',
                          groups: List[str]=list(), override: Union[bool, None]=None) -> None:
        pass

    def on_project_renamed(self, project_old_name: str, project_new_name: str) -> None:
        pass

    def on_project_removed(self, project_name: str) -> None:
        pass

    def on_remote_added(self, remote_name: str, remote_path: str) -> None:
        pass

    def on_remote_edit(self, remote_name: str, remote_path: str) -> None:
        pass

    def on_remote_removed(self, remote_name: str) -> None:
        pass

    def on_remote_renamed(self, remote_old_name: str, remote_new_name: str) -> None:
        pass

    def on_revision_added(self, revision_name: str, revision_type: str) -> None:
        pass

    def on_revision_edit(self, revision_name: str, revision_type: str) -> None:
        pass

    def on_revision_removed(self, revision_name: str) -> None:
        pass

    def on_revision_renamed(self, revision_old_name: str, revision_new_name: str) -> None:
        pass


if __name__ == '__main__':
    ManifestEditor(manifest.LocalManifest.from_revisions(configuration.Configuration.read_configuration(),
                                                         'generic-int', 'sailfish-7.1.1-int'))
