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
import json
import os
import shutil
import subprocess
import sys

from aospbuild import AOSPBuild
from aosptree import AOSPTree
from avbtool import AVBToolAdapter
from commandline import SignerCommandLineInterface
from configuration import Configuration
from sanity import SanityChecks


class Signer(object):

    _FEC = 'fec'

    @staticmethod
    def sign(configuration: Configuration, aosp_tree: AOSPTree, product_name: str, image_path: str, key_path: str,
             other_images_path: str, output_path: str) -> None:
        avb_repository_path = configuration.repository_avb().get_path_name()
        if avb_repository_path.startswith('platform/'):
            avb_repository_path = avb_repository_path[len('platform/'):]  # Path in AOSP.
        avb = AVBToolAdapter(os.path.join(aosp_tree.path(), avb_repository_path))

        with contexts.set_cwd(os.path.dirname(os.path.realpath(sys.argv[0]))):
            with open(configuration.signing_info()) as signing_info_file:
                signing_info = json.load(signing_info_file)
                hashtree_info = signing_info['add_hashtree_footer'][product_name]
                vbmeta_info = signing_info['make_vbmeta_image'][product_name]

        # Setup output directory.
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        # Rename on the fly to make sure the verification does not fail because the image is named differently.
        signed_image_path = os.path.join(output_path, '{}.img'.format(hashtree_info['partition_name']))
        shutil.copy(image_path, signed_image_path)
        for image_name in vbmeta_info['include_descriptors_from_image']:
            if image_name != os.path.basename(signed_image_path):  # Do not try to copy the image to sign.
                shutil.copy(os.path.join(other_images_path, image_name), output_path)

        # Add the hashtree footer to the image.
        with contexts.append_to_path(os.path.join(aosp_tree.path(), configuration.host_bin_path())):
            if hashtree_info['generate_fec']:  # Generate fec if it is needed.
                Signer._make_fec(configuration, aosp_tree, product_name)
            avb.add_hashtree_footer(signed_image_path, hashtree_info['partition_name'], hashtree_info['generate_fec'],
                                    hashtree_info['fec_num_roots'], hashtree_info['hash_algorithm'],
                                    hashtree_info['block_size'], hashtree_info['salt'], hashtree_info['algorithm'],
                                    hashtree_info['rollback_index'], hashtree_info['setup_as_rootfs_from_kernel'])

        # Generate the vbmeta image.
        images_paths = [os.path.join(output_path, image_name)
                        for image_name in vbmeta_info['include_descriptors_from_image']]
        avb.make_vbmeta_image(os.path.join(output_path, '{}.img'.format(vbmeta_info['partition_name'])),
                              vbmeta_info['algorithm'], key_path, vbmeta_info['rollback_index'], images_paths,
                              vbmeta_info['padding_size'])

        # Verify the images.
        with contexts.set_cwd(output_path):
            # The working directory must be set where the images actually are because avbtool tries to load them from
            # the current working directory by appending ``.img`` to the partition names found in vbmeta.
            avb.verify_image('{}.img'.format(vbmeta_info['partition_name']), key_path,
                             configuration.verify_timeout_sec())

    @staticmethod
    def _make_fec(configuration: Configuration, aosp_tree: AOSPTree, product_name: str) -> None:
        try:
            subprocess.check_call([Signer._FEC], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            # Exited because the arguments were missing, but the binary exists.
            return
        except FileNotFoundError:
            # The binary does not exist, make it.
            AOSPBuild.build(configuration, aosp_tree, Signer._FEC, product_name)


def main() -> None:
    SanityChecks.run()

    configuration = Configuration.read_configuration()
    cli = SignerCommandLineInterface(configuration)
    Signer.sign(configuration, AOSPTree(configuration, cli.path()), cli.product(), cli.image_path(), cli.key_path(),
                cli.other_images_path(), cli.output_path())


if __name__ == '__main__':
    main()
