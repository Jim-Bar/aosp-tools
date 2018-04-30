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

import collections
import configuration
import functools
import manifest
import urwid

from typing import Callable, Dict, Iterable, List, Tuple, Union


class _ToggleableText(urwid.SelectableIcon):
    """
    TODO
    """

    def __init__(self, text: str, is_toggled: bool, on_toggle: Callable[[bool], bool]) -> None:
        self._toggled = is_toggled
        self._on_toggled = on_toggle
        super().__init__(('toggled' if self._toggled else 'toggleable', text), 0)

    def keypress(self, size, key):
        if key == ' ':
            self._toggle()
            return None
        else:
            return super().keypress(size, key)

    def toggle_off(self) -> None:
        self._toggled = False
        self.set_text(('toggleable', self.text))

    def _toggle(self) -> None:
        if self._on_toggled(not self._toggled):
            self._toggled = not self._toggled
            self.set_text(('toggled' if self._toggled else 'toggleable', self.text))


class _PanelCategoryItem(urwid.Columns):
    """
    TODO
    """

    def __init__(self, first: str, second: str, formatter: Callable[[str, str], str], count: int,
                 is_toggled: bool, on_toggle: Callable[[bool], bool]) -> None:
        self._content_widget = _ToggleableText(formatter(first, second), is_toggled, on_toggle)
        count_widget = urwid.Text('[{}]'.format(count), align=urwid.RIGHT)
        super().__init__([
            (urwid.WEIGHT, 26, self._content_widget),
            (urwid.WEIGHT, 3, count_widget)
        ])

        self._first = first
        self._second = second

    def first(self) -> str:
        return self._first

    def second(self) -> str:
        return self._second

    def toggle_off(self) -> None:
        self._content_widget.toggle_off()


class _PanelCategory(urwid.Pile):
    """
    TODO
    """

    def __init__(self, category_name: str, items: List[Tuple[str, str, int]], formatter: Callable[[str, str], str],
                 on_widget_toggle: Callable[[str, bool], bool]) -> None:
        widget_title = urwid.Text(category_name)

        divider_widget = urwid.Divider()
        self._widgets = collections.OrderedDict()
        is_toggled = True
        for first, second, count in items:
            self._widgets[first] = _PanelCategoryItem(first, second, formatter, count, is_toggled,
                                                      functools.partial(on_widget_toggle, first))
            is_toggled = False

        super().__init__([
            widget_title,
            divider_widget,
            urwid.Pile([(urwid.PACK, remote_widget) for remote_widget in self._widgets.values()])
        ])

    def columns(self) -> int:
        required_widths = [len(widget.contents[0][0].text) + len(widget.contents[1][0].text) + 2
                           for widget, _ in self.contents[-1][0].contents]
        return max(required_widths)

    def get_widget(self, name: str) -> _PanelCategoryItem:
        return self._widgets[name]

    def get_widgets(self) -> Iterable[_PanelCategoryItem]:
        return self._widgets.values()


class _Panel(urwid.Pile):
    """
    TODO
    """

    _INFO = '(Action: SPACE, Edit: e, Add: +, Remove: -)'

    def __init__(self, groups: List[str], on_group_toggle: Callable[[str, bool], bool], remotes: List[Tuple[str, str]],
                 on_remote_toggle: Callable[[str, bool], bool], revisions: List[Tuple[str, str]],
                 on_revision_toggle: Callable[[str, bool], bool]) -> None:
        groups = [(group, '', 0) for group in groups]
        remotes = [(name, path, 0) for name, path in remotes]
        revisions = [(name, type_name, 0) for name, type_name in revisions]

        self._remotes = _PanelCategory('Remotes', remotes, lambda a, b: '{} -> {}'.format(a, b), on_remote_toggle)
        self._revisions = _PanelCategory('Revisions', revisions, lambda a, b: '{}/{}'.format(b, a), on_revision_toggle)
        self._groups = _PanelCategory('Groups', groups, lambda a, b: a, on_group_toggle)
        super().__init__([self._remotes, self._revisions, self._groups, urwid.Text(_Panel._INFO)])

    def columns(self) -> int:
        required_widths = [category.columns() for category, _ in self.contents
                           if type(category) is _PanelCategory]
        return max(required_widths)

    def groups(self) -> _PanelCategory:
        return self._groups

    def remotes(self) -> _PanelCategory:
        return self._remotes

    def revisions(self) -> _PanelCategory:
        return self._revisions


class _Max(object):
    """
    TODO
    """

    def __init__(self, max_name: int, max_path: int, max_revision: int, max_remote: int, max_groups: int) -> None:
        self._name = max_name
        self._path = max_path
        self._revision = max_revision
        self._remote = max_remote
        self._groups = max_groups

    def name(self) -> int:
        return self._name

    def path(self) -> int:
        return self._path

    def revision(self) -> int:
        return self._revision

    def remote(self) -> int:
        return self._remote

    def groups(self) -> int:
        return self._groups

    @staticmethod
    def max_length(projects: List[Tuple[str, str, bool, str, str, List[str]]], index: int, caption: str,
                   func: Callable[[Iterable[str]], str]=lambda x: x) -> int:
        return max(max(map(lambda item: len(func(item[index])), projects)), len(caption))


class _Project(urwid.SelectableIcon):
    """
    TODO
    """

    def __init__(self, name: str, path: str, override: bool, revision: str, remote: str, groups: List[str],
                 maximums: _Max) -> None:
        self._name = name
        self._path = path
        self._override = override
        self._revision = revision
        self._remote = remote
        self._groups = groups
        super().__init__(self._build_text(maximums), cursor_position=0)

    def _build_text(self, maximums: _Max) -> str:
        return '{} {} {} {} {} {}'.format('*' if self._override else ' ', self._name.ljust(maximums.name()),
                                          self._path.ljust(maximums.path()), self._revision.ljust(maximums.revision()),
                                          self._remote.ljust(maximums.remote()),
                                          ','.join(self._groups).ljust(maximums.groups()))


class _ProjectList(urwid.Pile):
    """
    TODO
    """

    def __init__(self, projects: List[Tuple[str, str, bool, str, str, List[str]]]) -> None:
        self._projects = dict()

        self._max = _Max(_Max.max_length(projects, 0, 'name'), _Max.max_length(projects, 1, 'path'),
                         _Max.max_length(projects, 3, 'revision'), _Max.max_length(projects, 4, 'remote'),
                         _Max.max_length(projects, 5, 'groups', ','.join))

        for name, path, override, revision, remote, groups in projects:
            self._projects[name] = _Project(name, path, override, revision, remote, groups, self._max)

        super().__init__([
            urwid.Text('  {} {} {} {} {}'.format('name'.ljust(self._max.name(), ' '),
                                                 'path'.ljust(self._max.path(), ' '),
                                                 'revision'.ljust(self._max.revision(), ' '),
                                                 'remote'.ljust(self._max.remote(), ' '),
                                                 'groups'.ljust(self._max.groups(), ' '))),
            urwid.Pile(self._projects.values())
        ])

    def projects(self) -> Dict[str, _Project]:
        return self._projects


class _GUI(object):
    """
    TODO
    """

    def __init__(self, projects: List[Tuple[str, str, bool, str, str, List[str]]], remotes: List[Tuple[str, str]],
                 revisions: List[Tuple[str, str]]) -> None:
        self._projects_widget = _ProjectList(projects)
        groups = set()
        for project in projects:
            groups.update(project[-1])
        groups = list(groups)

        groups.sort()
        remotes.sort()
        revisions.sort()

        self._panel = _Panel(groups, self._on_group_toggle, remotes, self._on_remote_toggle, revisions,
                             self._on_revision_toggle)
        self._selected_remote = remotes[0][0]
        self._selected_revision = revisions[0][0]
        self._selected_groups = {groups[0]}

        palette = [
            ('toggleable', 'default', 'default'),
            ('toggled', 'standout', 'default')
        ]

        urwid.MainLoop(urwid.Columns([
            urwid.Filler(self._projects_widget, urwid.TOP),
            (self._panel.columns(), urwid.Filler(self._panel, urwid.TOP))
        ]), palette).run()

    def _on_remote_toggle(self, remote_name: str, will_be_toggled: bool) -> bool:
        if not will_be_toggled:  # Remotes cannot be unselected.
            return False

        for remote in self._panel.remotes().get_widgets():
            if remote_name != remote.first():
                remote.toggle_off()

        return True

    def _on_revision_toggle(self, revision_name: str, will_be_toggled: bool) -> bool:
        if not will_be_toggled:  # Revisions cannot be unselected.
            return False

        for revision in self._panel.revisions().get_widgets():
            if revision_name != revision.first():
                revision.toggle_off()

        return True

    def _on_group_toggle(self, group_name: str, will_be_toggled: bool) -> bool:
        return True  # Nothing to do, several groups can be selected at once.


class ManifestEditor(object):
    """
    Link between the local manifest object and urwid.
    """

    def __init__(self, local_manifest: manifest.LocalManifest) -> None:
        projects = [(project.name(), project.path(), project.override(), project.ref().name(), project.remote().name(),
                     project.groups()) for project in local_manifest.projects()]
        remotes = [(remote.name(), remote.path()) for remote in local_manifest.remotes()]
        revisions = [(ref.name(), ref.type()) for ref in local_manifest.refs()]
        _GUI(projects, remotes, revisions)

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
