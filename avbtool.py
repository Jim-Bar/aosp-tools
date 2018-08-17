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

import os
import subprocess
import sys

from typing import List


class AVBToolAdapter(object):
    """
    This adapter is required because ``avbtool`` is written in Python 2 and using ``lib2to3`` on the fly is not possible
    unless fixers are added to it, which is a hassle. Consequently we use this adapter instead which calls ``avbtool``
    as a binary directly.
    """

    _AVBTOOL = 'avbtool'

    def __init__(self, avbtool_path: str) -> None:
        self._avbtool_path = os.path.join(avbtool_path, AVBToolAdapter._AVBTOOL)

    def add_hashtree_footer(self, sparse_image_path: str, partition_name: str, generate_fec: bool, fec_num_roots: int,
                            hash_algorithm: str, block_size: int, salt: str, algorithm: str, rollback_index: int,
                            setup_as_rootfs_from_kernel: bool) -> int:
        """
        Add a security metadata hashtree footer to the provided image. Refer to ``avbtool`` for more information. The
        binary ``fec`` must be available (in the PATH) if the parameter ``generate_fec`` is ``True``.

        :param sparse_image_path: the path to the sparse image file on which to add the footer.
        :param partition_name: the name of the partition contained in the image file.
        :param generate_fec: whether to generate Forward Error Correction (FEC) code. Refer to ``avbtool``.
        :param fec_num_roots: number of roots for FEC. Refer to ``avbtool``.
        :param hash_algorithm: name of the hash algorithm as recognized by ``hashlib``.
        :param block_size: size of the blocks.
        :param salt: salt to use when generating hashes.
        :param algorithm: signing algorithm to use. Refer to ``avbtool``.
        :param rollback_index: rollback index. Refer to ``avbtool``.
        :param setup_as_rootfs_from_kernel: refer to ``avbtool``.
        :return: the exit code of ``avbtool``.
        """
        ext4_image_size = AVBToolAdapter._sparse_image_original_size(sparse_image_path)
        partition_size = self._compute_partition_size(ext4_image_size, generate_fec, fec_num_roots, hash_algorithm,
                                                      block_size)

        cmd = [
            self._avbtool_path,
            'add_hashtree_footer',
            '--image', sparse_image_path,
            '--partition_size', str(partition_size),
            '--partition_name', partition_name,
            '--hash_algorithm', hash_algorithm,
            '--salt', salt,
            '--block_size', str(block_size),
            '--algorithm', algorithm if algorithm else 'NONE',
            '--rollback_index', str(rollback_index)
        ]

        if generate_fec:
            cmd.extend(['--fec_num_roots', str(fec_num_roots)])

        if setup_as_rootfs_from_kernel:
            cmd.append('--setup_as_rootfs_from_kernel')

        return subprocess.check_call(cmd)

    def make_vbmeta_image(self, vbmeta_image_path: str, algorithm: str, key_path: str, rollback_index: int,
                          descriptors_from_image: List[str], padding_size: int) -> int:
        cmd = [
            self._avbtool_path,
            'make_vbmeta_image',
            '--padding_size', str(padding_size),
            '--algorithm', algorithm if algorithm else 'NONE',
            '--key', key_path,
            '--rollback_index', str(rollback_index),
            '--output', vbmeta_image_path
        ]

        for image_path in descriptors_from_image:
            cmd.append('--include_descriptors_from_image')
            cmd.append(image_path)

        return subprocess.check_call(cmd)

    def verify_image(self, image_path: str, key_path: str, timeout_sec: int) -> int:
        cmd = [
            self._avbtool_path,
            'verify_image',
            '--image', image_path,
            '--key', key_path
        ]
        try:
            return subprocess.check_call(cmd, timeout_sec)
        except subprocess.TimeoutExpired:
            raise RuntimeError('Verification of image {} failed (timeout of {} seconds reached)'
                               .format(os.path.basename(image_path), timeout_sec))

    def _compute_partition_size(self, ext4_image_size: int, generate_fec: bool, fec_num_roots: int,
                                hash_algorithm: str, block_size: int) -> int:
        """
        Compute the size of the partition required for holding the image and its security metadata.

        :param ext4_image_size: size of the ext4 image.
        :param generate_fec: if FEC is used for generating the metadata.
        :param fec_num_roots: the number of roots for FEC if it is used, ignored otherwise.
        :param hash_algorithm: name of the hash algorithm used for generating the metadata.
        :param block_size: size of the blocks in bytes.
        :return: the required size of the partition for containing the image plus its metadata.
        """
        partition_size = ext4_image_size

        while partition_size - self._metadata_size(partition_size, generate_fec, fec_num_roots, hash_algorithm,
                                                   block_size) < ext4_image_size:
            partition_size = ext4_image_size + self._metadata_size(partition_size, generate_fec, fec_num_roots,
                                                                   hash_algorithm, block_size)

        return partition_size

    def _metadata_size(self, partition_size: int, generate_fec: bool, fec_num_roots: int, hash_algorithm: str,
                       block_size: int) -> int:
        """
        Compute the size of the security metadata of a partition.

        :param partition_size: size of the partition.
        :param generate_fec: if FEC is used for generating the metadata.
        :param fec_num_roots: the number of roots for FEC if it is used, ignored otherwise.
        :param hash_algorithm: name of the hash algorithm used for generating the metadata.
        :param block_size: size of the blocks in bytes.
        :return: the size of the metadata for the provided partition.
        """

        cmd = [
            self._avbtool_path,
            'add_hashtree_footer',
            '--partition_size', str(partition_size),
            '--hash_algorithm', hash_algorithm,
            '--block_size', str(block_size),
            '--calc_max_image_size'
        ]

        if generate_fec:
            cmd.extend(['--fec_num_roots', str(fec_num_roots)])

        return partition_size - int(subprocess.check_output(cmd))

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
