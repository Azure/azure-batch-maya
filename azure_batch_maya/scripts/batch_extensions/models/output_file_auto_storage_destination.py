# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from msrest.serialization import Model


class OutputFileAutoStorageDestination(Model):
    """An speficition of output files upload destination that uses an
    auto-storage file group.

    :param str file_group: The name of the file group that the output files will
     be uploaded to.
    :param str path: The destination path within the file group that the files will
     be uploaded to. Is the output file specification refers to a single file, this will
     be treated as a file name. If the output file specification refers to potentially
     multiple files, this will be treated as a subfolder.
    """

    _validation = {
        'file_group': {'required': True}
    }

    _attribute_map = {
        'file_group': {'key': 'fileGroup', 'type': 'str'},
        'path': {'key': 'path', 'type': 'str'},
    }

    def __init__(self, file_group, path=None):
        self.file_group = file_group
        self.path = path
