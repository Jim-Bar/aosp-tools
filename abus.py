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

import json

from adb import ADBAdapter


class ABusAdapter(object):
    """
    Provides utility functions for issuing A-Bus commands.
    """

    _ABUS = 'abus_send'
    _METHOD_FORMAT = 'amaCnxMgr.{}.{}'
    _PARAMS_FORMAT = "params:s='{}'"

    @staticmethod
    def request(module_name, method_name, parameters):
        answer = ADBAdapter.shell(ABusAdapter._ABUS, ABusAdapter._METHOD_FORMAT.format(module_name, method_name),
                                  ABusAdapter._PARAMS_FORMAT.format(json.dumps(parameters)))
        if answer.startswith('error'):
            return None
        else:
            return json.loads(answer.split('=', 1).pop()[1:-1])
