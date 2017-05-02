# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from .task_factory_base import TaskFactoryBase


class ParametricSweepTaskFactory(TaskFactoryBase):
    """A Task Factory for generating a set of tasks based on one or more parameter
    sets to define a numeric input range. Each parameter set will have a start, end
    and step value. A task will be generated for each integer in this range. Multiple
    parameter sets can be combined for a multi-dimensional sweep.

    :param parameter_sets: A list if parameter sets from which tasks will be generated.
    :type parameter_sets: A list of :class:`ParameterSet<azure.batch_extensions.models.ParameterSet>`
    :param repeat_task: The task template the will be used to generate each task.
    :type repeat_task: :class:`RepeatTask <azure.batch_extensions.models.RepeatTask>`
    :param merge_task: An optional additional task to be run after all the other
     generated tasks have completed successfully.
    :type merge_task: :class:`MergeTask <azure.batch_extensions.models.MergeTask>`
    """

    _validation = {
        'type': {'required': True},
        'parameter_sets': {'required': True, 'min_items': 1},
        'repeat_task': {'required': True}
    }

    _attribute_map = {
        'type': {'key': 'type', 'type': 'str'},
        'parameter_sets': {'key': 'parameterSets', 'type': '[ParameterSet]'},
        'repeat_task': {'key': 'repeatTask', 'type': 'RepeatTask'},
        'merge_task': {'key': 'mergeTask', 'type': 'MergeTask'}
    }

    def __init__(self, parameter_sets, repeat_task, merge_task=None):
        super(ParametricSweepTaskFactory, self).__init__(merge_task)
        if not parameter_sets:
            raise ValueError("Parametric Sweep task factory requires at least one parameter set.")
        self.parameter_sets = parameter_sets
        self.repeat_task = repeat_task
        self.type = 'parametricSweep'
