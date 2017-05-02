# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from .task_factory_base import TaskFactoryBase


class FileCollectionTaskFactory(TaskFactoryBase):
    """A Task Factory for generating a set of tasks based on the contents
    of an Azure Storage container or auto-storage file group. One task
    will be generated per input file, and automatically added to the job.

    :param source: The input file source from which the tasks will be generated.
    :type source: :class:`FileSource <azure.batch_extensions.models.FileSource>`
    :param repeat_task: The task template the will be used to generate each task.
    :type repeat_task: :class:`RepeatTask <azure.batch_extensions.models.RepeatTask>`
    :param merge_task: An optional additional task to be run after all the other
     generated tasks have completed successfully.
    :type merge_task: :class:`MergeTask <azure.batch_extensions.models.MergeTask>`
    """

    _validation = {
        'type': {'required': True},
        'source': {'required': True},
        'repeat_task': {'required': True}
    }

    _attribute_map = {
        'type': {'key': 'type', 'type': 'str'},
        'source': {'key': 'source', 'type': 'FileSource'},
        'repeat_task': {'key': 'repeatTask', 'type': 'RepeatTask'},
        'merge_task': {'key': 'mergeTask', 'type': 'MergeTask'}
    }

    def __init__(self, source, repeat_task, merge_task=None):
        super(FileCollectionTaskFactory, self).__init__(merge_task)
        self.source = source
        self.repeat_task = repeat_task
        self.type = 'taskPerFile'
