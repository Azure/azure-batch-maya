# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from msrest.serialization import Model


class FileSource(Model):
    """A source of input files to be downloaded onto a compute node.

    :param str file_group: The name of an auto-storage file group.
    :param str url: The URL of a file to be downloaded.
    :param str container_url: The SAS URL of an Azure Storage container.
    :param str prefix: The filename prefix or subdirectory of input files
     in either an auto-storage file group or container. Will be ignored if
     conbined with url.
    """

    _attribute_map = {
        'file_group': {'key': 'fileGroup', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'},
        'container_url': {'key': 'containerUrl', 'type': 'str'},
        'prefix': {'key': 'prefix', 'type': 'str'},
    }

    def __init__(self, file_group=None, url=None, container_url=None, prefix=None):
        self.file_group = file_group
        self.url = url
        self.container_url = container_url
        self.prefix = prefix
