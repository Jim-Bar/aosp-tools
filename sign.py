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

import hashlib
import importlib.machinery
import importlib.util
import json
import lib2to3.main
import os
import sys
import tempfile

from aosptree import AOSPTree
from configuration import Configuration


class Signer(object):

    _AVBTOOL = 'avbtool'

    def __init__(self, configuration: Configuration, aosp_tree: AOSPTree) -> None:
        self._configuration = configuration

        # The tool avbtool is for Python 2. Run 2to3 on it, save the result in temporary files and run it from there.
        avbtool_suffix = '{}.py'.format(aosp_tree.revision())
        avbtool_path = os.path.join(tempfile.gettempdir(), '{}.{}'.format(Signer._AVBTOOL, avbtool_suffix))
        if not os.path.exists(avbtool_path):  # The file is never deleted so it could already exist.
            lib2to3_args = [
                '-w',  # Write back modified files.
                '-W',  # Also write files even if no changes were required (useful with --output-dir); implies -w.
                '-n',  # Don't write backups for modified files.
                '--add-suffix=.{}'.format(avbtool_suffix),  # Append this string to all output file names. Requires -n.
                '-o',  # Put output files in this directory instead of overwriting the input files. Requires -n.
                tempfile.gettempdir(),
                os.path.join(aosp_tree.path(), configuration.repository_avb().get_path_name(), Signer._AVBTOOL)
            ]
            lib2to3.main.main('lib2to3.fixes', lib2to3_args)

            # And now an awful fix for byte arrays which only accept bytes in Python 3 (and no more strings). Doing this
            # is a lot easier than adding a new fixer to lib2to3 but if new fixes are required it could be better to
            # properly implementing fixers.
            with open(avbtool_path) as avbtool_file:
                avbtool_source_code = avbtool_file.read()
            avbtool_source_code = avbtool_source_code\
                .replace("data.extend('\\0' * chunk_pos_to_go)", "data.extend(b'\\0' * chunk_pos_to_go)")\
                .replace("salt = salt.decode('hex')", "salt = salt")
            with open(avbtool_path, 'w') as avbtool_file:
                avbtool_file.write(avbtool_source_code)
        os.chmod(avbtool_path, 0o644)  # Remove execution rights which are not needed.

        # Import dynamically from path: https://stackoverflow.com/a/67692 and https://stackoverflow.com/a/51575963
        importlib.machinery.SOURCE_SUFFIXES.append('')
        try:
            spec = importlib.util.spec_from_file_location(Signer._AVBTOOL, avbtool_path)
            self._avbtool = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self._avbtool)
        finally:
            importlib.machinery.SOURCE_SUFFIXES.pop()

    def sign(self, product_name: str, sparse_image_path: str, key_path: str, vbmeta_image_path: str,
             other_images_path: str) -> None:
        avb = self._avbtool.Avb()
        with open(self._configuration.signing_info()) as signing_info_file:
            signing_info = json.load(signing_info_file)
            hashtree_info = signing_info['add_hashtree_footer'][product_name]
            vbmeta_info = signing_info['make_vbmeta_image'][product_name]

        # Add the hashtree footer to the image.
        partition_size = self._compute_partition_size(self._sparse_image_original_size(sparse_image_path),
                                                      hashtree_info['generate_fec'], hashtree_info['fec_num_roots'],
                                                      hashtree_info['block_size'], hashtree_info['hash_algorithm'])
        avb.add_hashtree_footer(sparse_image_path,  # image_filename
                                partition_size,  # partition_size
                                hashtree_info['partition_name'],  # partition_name
                                hashtree_info['generate_fec'],  # generate_fec
                                hashtree_info['fec_num_roots'],  # fec_num_roots
                                hashtree_info['hash_algorithm'],  # hash_algorithm
                                hashtree_info['block_size'],  # block_size
                                hashtree_info['salt'],  # salt
                                None,  # chain_partitions
                                hashtree_info['algorithm'],  # algorithm_name
                                key_path,  # key_path
                                None,  # public_key_metadata_path
                                hashtree_info['rollback_index'],  # rollback_index
                                None,  # flags
                                list(),  # props
                                list(),  # props_from_file
                                list(),  # kernel_cmdlines
                                None,  # setup_rootfs_from_kernel
                                hashtree_info['setup_as_rootfs_from_kernel'],  # setup_as_rootfs_from_kernel
                                list(),  # include_descriptors_from_image
                                False,  # calc_max_image_size
                                None,  # signing_helper
                                None,  # signing_helper_with_files
                                None,  # release_string
                                None,  # append_to_release_string
                                None,  # output_vbmeta_image
                                False,  # do_not_append_vbmeta_image
                                False)  # print_required_libavb_version

        # Generate the vbmeta image.
        descriptors_from_image = [open(os.path.join(other_images_path, file_path)) for file_path
                                  in vbmeta_info['include_descriptors_from_image']]
        avb.make_vbmeta_image(vbmeta_image_path,  # output
                              None,  # chain_partitions
                              vbmeta_info['algorithm'],  # algorithm_name
                              key_path,  # key_path
                              None,  # public_key_metadata_path
                              vbmeta_info['rollback_index'],  # rollback_index
                              None,  # flags
                              list(),  # props
                              list(),  # props_from_file
                              list(),  # kernel_cmdlines
                              None,  # setup_rootfs_from_kernel
                              descriptors_from_image,  # include_descriptors_from_image
                              None,  # signing helper
                              None,  # signing_helper_with_files
                              None,  # release_string
                              None,  # append_to_release_string
                              False,  # print_required_libavb_version
                              vbmeta_info['padding_size'])  # padding_size

        # Verify the images.
        # TODO: do.

    def _compute_partition_size(self, ext4_image_size: int, generate_fec: bool, fec_num_roots: int, block_size: int,
                                hash_algorithm: str) -> int:
        """
        Compute the size of the partition required for holding the image and its security metadata.

        :param ext4_image_size: size of the ext4 image.
        :param generate_fec: if FEC is used for generating the metadata.
        :param fec_num_roots: the number of roots for FEC if it is used, ignored otherwise.
        :param block_size: size of the blocks in bytes.
        :param hash_algorithm: name of the hash algorithm used for generating the metadata.
        :return: the required size of the partition for containing the image plus its metadata.
        """
        partition_size = ext4_image_size

        while partition_size - self._metadata_size(partition_size, generate_fec, fec_num_roots, block_size,
                                                   hash_algorithm) < ext4_image_size:
            partition_size = ext4_image_size + self._metadata_size(partition_size, generate_fec, fec_num_roots,
                                                                   block_size, hash_algorithm)

        return partition_size

    def _metadata_size(self, partition_size: int, generate_fec: bool, fec_num_roots: int, block_size: int,
                       hash_algorithm: str) -> int:
        """
        Compute the size of the security metadata of a partition.

        :param partition_size: size of the partition.
        :param generate_fec: if FEC is used for generating the metadata.
        :param fec_num_roots: the number of roots for FEC if it is used, ignored otherwise.
        :param block_size: size of the blocks in bytes.
        :param hash_algorithm: name of the hash algorithm used for generating the metadata.
        :return: the size of the metadata for the provided partition.
        """
        # FEC metadata size.
        if generate_fec:
            fec_size = self._avbtool.calc_fec_data_size(partition_size, fec_num_roots)
        else:
            fec_size = 0

        # Hash tree metadata size.
        digest_size = len(hashlib.new(name=hash_algorithm).digest())
        digest_padding = self._avbtool.round_to_pow2(digest_size) - digest_size
        tree_size = int(self._avbtool.calc_hash_level_offsets(partition_size, block_size,
                                                              digest_size + digest_padding)[-1])

        return self._avbtool.Avb.MAX_VBMETA_SIZE + self._avbtool.Avb.MAX_FOOTER_SIZE + fec_size + tree_size

    @staticmethod
    def _sparse_image_original_size(sparse_image_path: str) -> int:
        """
        Read a sparse image for finding out the size of the original ext4 image. For the header structure of sparse
        images, refer to ``system/core/libsparse/sparse_format.h`` in the AOSP.

        :param sparse_image_path: path to the sparse image.
        :return: the size of the ext4 image.
        """
        with open(sparse_image_path, 'rb') as sparse_image:
            sparse_image.seek(12)
            block_size = int.from_bytes(sparse_image.read(4), byteorder=sys.byteorder)
            total_blocks = int.from_bytes(sparse_image.read(4), byteorder=sys.byteorder)

        return block_size * total_blocks


def main() -> None:
    configuration = Configuration.read_configuration()
    signer = Signer(configuration, AOSPTree(configuration, '2018-08-10_12-45-02_android-8.1.0_r41'))
    signer.sign('enchilada', '2018-08-10_12-45-02_android-8.1.0_r41/out/target/product/enchilada/system.img',
                '2018-08-10_12-45-02_android-8.1.0_r41/external/avb/test/data/testkey_rsa4096.pem', 'vbmeta.img',
                'official')


if __name__ == '__main__':
    main()
