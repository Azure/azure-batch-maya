# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from azure.batch.models import ResourceFile


class ExtendedResourceFile(ResourceFile):
    """A file to be downloaded from Azure blob storage to a compute node.

    :param blob_source: The URL of the file within Azure Blob Storage. This
     URL must be readable using anonymous access; that is, the Batch service
     does not present any credentials when downloading the blob. There are two
     ways to get such a URL for a blob in Azure storage: include a Shared
     Access Signature (SAS) granting read permissions on the blob, or set the
     ACL for the blob or its container to allow public access.
    :type blob_source: str
    :param file_path: The location on the compute node to which to download
     the file, relative to the task's working directory. If using a file group
     source that references more than one file, this will be considered the name
     of a directory, otherwise it will be treated as the destination file name.
    :type file_path: str
    :param file_mode: The file permission mode attribute in octal format. This
     property applies only to files being downloaded to Linux compute nodes. It
     will be ignored if it is specified for a resourceFile which will be
     downloaded to a Windows node. If this property is not specified for a
     Linux node, then a default value of 0770 is applied to the file.
     If using a file group source that references more than one file, this will be
     applied to all files in the group.
    :type file_mode: str
    :param source: A file source reference which could include a collection of files from
     a Azure Storage container or an auto-storage file group.
    :type source: :class:`FileSource
     <azure.batch_extensions.models.FileSource>`
    """

    _attribute_map = {
        'blob_source': {'key': 'blobSource', 'type': 'str'},
        'file_path': {'key': 'filePath', 'type': 'str'},
        'file_mode': {'key': 'fileMode', 'type': 'str'},
        'source': {'key': 'source', 'type': 'FileSource'}
    }

    def __init__(self, blob_source=None, file_path=None, file_mode=None, source=None):
        super(ExtendedResourceFile, self).__init__(blob_source, file_path, file_mode)
        self.source = source
