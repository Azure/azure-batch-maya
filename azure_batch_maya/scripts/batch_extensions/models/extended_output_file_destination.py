# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from msrest.serialization import Model


class ExtendedOutputFileDestination(Model):
    """The specification for where output files should be uploaded to on task
    completion.

    :param container: A location in Azure blob storage to which files are
     uploaded. This cannot be combined with auto_storage.
    :type container: :class:`OutputFileBlobContainerDestination
     <azure.batch_extensions.models.OutputFileBlobContainerDestination>`
    :param auto_storage: An auto-storage file group reference. This cannot be
     combined with container.
    :type auto_storage: :class:`OutputFileAutoStorageDestination
     <azure.batch_extensions.models.OutputFileAutoStorageDestination>`
    """

    _attribute_map = {
        'container': {'key': 'container', 'type': 'OutputFileBlobContainerDestination'},
        'auto_storage': {'key': 'autoStorage', 'type': 'OutputFileAutoStorageDestination'},
    }

    def __init__(self, container=None, auto_storage=None):
        if container and auto_storage:
            raise ValueError("Cannot specify both container and auto_storage.")
        self.container = container
        self.auto_storage = auto_storage
