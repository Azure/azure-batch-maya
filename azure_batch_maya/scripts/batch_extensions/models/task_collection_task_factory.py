# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from .task_factory_base import TaskFactoryBase


class TaskCollectionTaskFactory(TaskFactoryBase):
    """A Task Factory for adding a predefined collection of tasks automatically
    to a job on submission.

    :param tasks: A list if task parameters, each of which will be added straight to the job.
    :type tasks: A list of :class:`ExtendedTaskParameter
     <azure.batch_extensions.models.ExtendedTaskParameter>`
    """

    _validation = {
        'type': {'required': True},
        'tasks': {'required': True},
    }

    _attribute_map = {
        'type': {'key': 'type', 'type': 'str'},
        'tasks': {'key': 'tasks', 'type': '[ExtendedTaskParameter]'},
    }

    def __init__(self, tasks):
        super(TaskCollectionTaskFactory, self).__init__()
        self.tasks = tasks
        self.type = 'taskCollection'
