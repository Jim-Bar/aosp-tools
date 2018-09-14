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

import contexts
import getpass
import os
import subprocess

from aospbuild import AOSPBuild
from aospspec import AOSPSpec
from aosptree import AOSPTree
from commandline import SignerCommandLineInterface
from configuration import Configuration
from sanity import SanityChecks


class Signer(object):
    """
    Generate the signed files from a target file:

    - signed target file
    - signed image file
    - signed OTA file

    The images/OTAs must be signed for release. See also: https://source.android.com/devices/tech/ota/sign_builds
    """

    # The script ``brillo_update_payload`` is a dependency of the signer scripts but is not built by default.
    _BRILLO_UPDATE_PAYLOAD = 'brillo_update_payload'

    def __init__(self, key_path: str) -> None:
        self._key_path = key_path

    def sign(self, configuration: Configuration, aosp_tree: AOSPTree) -> None:
        with contexts.set_cwd(aosp_tree.path()):
            # Build `brillo_update_payload`` if it has not been built yet.
            if not os.path.isfile(os.path.join(configuration.host_bin_path(), Signer._BRILLO_UPDATE_PAYLOAD)):
                AOSPBuild(Signer._BRILLO_UPDATE_PAYLOAD).build(configuration, aosp_tree)

            aosp_spec = AOSPSpec.from_aosp_tree(aosp_tree)

            target_file_name = '{}-target_files-eng.{}.zip'.format(aosp_spec.product(), getpass.getuser())
            signed_target_file_name = '{}-signed_target_files-eng.{}.zip'.format(aosp_spec.product(), getpass.getuser())
            signed_image_file_name = '{}-signed_img-eng.{}.zip'.format(aosp_spec.product(), getpass.getuser())
            signed_ota_file_name = '{}-signed_ota-eng.{}.zip'.format(aosp_spec.product(), getpass.getuser())
            target_file_path = os.path.join(configuration.dist_path(), target_file_name)
            signed_target_file_path = os.path.join(configuration.dist_path(), signed_target_file_name)
            signed_image_file_path = os.path.join(configuration.dist_path(), signed_image_file_name)
            signed_ota_file_path = os.path.join(configuration.dist_path(), signed_ota_file_name)

            # Sign target file.
            if os.path.exists(signed_target_file_path):
                os.remove(signed_target_file_path)
            subprocess.check_call([os.path.join(configuration.release_tools_path(), 'sign_target_files_apks'), '-o',
                                   '-d', self._key_path, target_file_path, signed_target_file_path])

            # Sign image file.
            if os.path.exists(signed_image_file_path):
                os.remove(signed_image_file_path)
            subprocess.check_call([os.path.join(configuration.release_tools_path(), 'img_from_target_files'),
                                   signed_target_file_path, signed_image_file_path])

            # Sign OTA file.
            if os.path.exists(signed_ota_file_path):
                os.remove(signed_ota_file_path)
            subprocess.check_call([os.path.join(configuration.release_tools_path(), 'ota_from_target_files'), '-k',
                                   os.path.join(self._key_path, 'releasekey'), signed_target_file_path,
                                   signed_ota_file_path])


def main() -> None:
    SanityChecks.run()

    configuration = Configuration()
    cli = SignerCommandLineInterface(configuration)
    signer = Signer(cli.key_path())
    signer.sign(configuration, AOSPTree(cli.path()))


if __name__ == '__main__':
    main()
