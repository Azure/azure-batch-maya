# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from msrest.serialization import Model


class ParameterSet(Model):
    """A set of parametric sweep range range parameters.

    :param int start: The starting value of the sweep.
    :param int end: The ending value of the sweep (inclusive).
    :param int step: The incremental step value, default is 1. The step value
     can be negative (i.e. a decending sweep), but only id the start value is
     a higher value than the end.
    """

    _validation = {
        'start': {'required': True},
        'end': {'required': True},
    }

    _attribute_map = {
        'start': {'key': 'start', 'type': 'int'},
        'end': {'key': 'end', 'type': 'int'},
        'step': {'key': 'step', 'type': 'int'},
    }

    def __init__(self, start, end, step=1):
        try:
            self.start = int(start)
            self.end = int(end)
            self.step = int(step)
        except (TypeError, ValueError):
            raise ValueError("'start', 'end' and 'step' parameters must be integers.")
        if step == 0:
            raise ValueError("'step' parameter cannot be 0.")
        elif start > end and step > 0:
            raise ValueError(
                "'step' must be a negative number when 'start' is greater than 'end'")
        elif start < end and step < 0:
            raise ValueError(
                "'step' must be a positive number when 'end' is greater than 'start'")
