# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from msrest.serialization import Model


class TaskFactoryBase(Model):
    """A Task Factory for automatically adding a collection of tasks to a job on
    submission.

    :param merge_task: An optional additional task to be run after all the other
     generated tasks have completed successfully.
    :type merge_task: :class:`MergeTask <azure.batch_extensions.models.MergeTask>`
    """

    _validation = {
        'type': {'required': True},
    }

    _attribute_map = {
        'type': {'key': 'type', 'type': 'str'},
        'merge_task': {'key': 'mergeTask', 'type': 'MergeTask'}
    }

    _subtype_map = {
        'type': {'parametricSweep': 'ParametricSweepTaskFactory',
                 'taskPerFile': 'FileCollectionTaskFactory',
                 'taskCollection': 'TaskCollectionTaskFactory'}
    }

    def __init__(self, merge_task=None):
        self.merge_task = merge_task
        self.type = None
