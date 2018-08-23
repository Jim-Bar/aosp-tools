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

from typing import Dict, List


@contextlib.contextmanager
def set_variable(variable: str, value: str) -> None:
    """
    Add the provided variable to the environment for the context scope only. If the variable is already defined, it will
    be overwritten.

    :param variable: name of the variable to set.
    :param value: value for the variable. When leaving the context, the value of the variable is restored.
    """
    with set_variables({variable: value}):
        yield


@contextlib.contextmanager
def set_variables(variables: Dict[str, str]) -> None:
    """
    Add the provided variables to the environment for the context scope only. If some variables are already defined,
    they will be overwritten.

    :param variables: a dictionary containing the variables' names as keys, and their new values as values. When leaving
                      the context, the values of the variables are restored.
    """
    previous_variables = dict()
    for variable in variables:
        previous_variables[variable] = os.environ.get(variable)
    try:
        for variable, value in variables.items():
            os.environ[variable] = value
        yield
    finally:
        for variable in variables:
            # None means the variable was not defined at all. If an exception arises in the try block, the variable
            # could not be in the environment, so we have to check for that as well.
            if variable in os.environ and previous_variables[variable] is None:
                del os.environ[variable]
            else:
                os.environ[variable] = previous_variables[variable]


@contextlib.contextmanager
def append_to_path(path: str) -> None:
    """
    Add the provided path to the PATH for the context scope only.

    :param path: the directory to add to the PATH. When leaving the context, the directory is removed from the PATH.
    """
    with set_variable('PATH', '{}:{}'.format(os.environ.get('PATH'), path)):
        yield


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


@contextlib.contextmanager
def unset_variable(variable: str) -> None:
    """
    Unset the provided variable for the context scope only. It has no effect if the variable is not already defined.

    :param variable: name of the variable to unset. When leaving the context, the variable is restored.
    """
    with unset_variables([variable]):
        yield


@contextlib.contextmanager
def unset_variables(variables: List[str]) -> None:
    """
    Unset the provided variables for the context scope only. It has no effect on variables which are not already
    defined.

    :param variables: list of the variables to unset. When leaving the context, the variables are restored to what they
                      were.
    """
    previous_variables = dict()
    for variable in variables:
        previous_variables[variable] = os.environ.get(variable)
    try:
        for variable in variables:
            if previous_variables[variable] is not None:  # None means the variable was not defined at all.
                del os.environ[variable]
        yield
    finally:
        for variable in variables:
            if previous_variables[variable] is not None:
                os.environ[variable] = previous_variables[variable]
