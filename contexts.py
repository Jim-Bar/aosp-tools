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
import sys


@contextlib.contextmanager
def append_to_path(path: str) -> None:
    """
    Add the provided path to the PATH for the context scope only.

    :param path: the directory to add to the PATH. When leaving the context, the directory is removed from the PATH.
    """
    previous_path = os.environ.get('PATH')
    try:
        os.environ['PATH'] = '{}:{}'.format(previous_path, path)
        yield
    finally:
        os.environ['PATH'] = previous_path


@contextlib.contextmanager
def open_local(*args, **kwargs) -> None:
    """
    Open a file located in the calling script's directory. Used as ``open``. This function makes difference only if
    called with a relative path. It will act exactly as ``open`` if given an absolute path.

    :param args: arguments passed to the built-in ``open``.
    :param kwargs: keywords arguments passed to the built-in ``open``.
    """
    with set_cwd(os.path.dirname(os.path.realpath(sys.argv[0]))):
        with open(*args, **kwargs) as file_object:
            yield file_object


@contextlib.contextmanager
def set_cwd(cwd: str) -> None:
    """
    Change the current working directory for the context scope only.

    :param cwd: new working directory. When leaving the context, the working directory is restored to what it was.
    """
    previous_cwd = os.getcwd()
    try:
        os.chdir(cwd)
        yield
    finally:
        os.chdir(previous_cwd)
