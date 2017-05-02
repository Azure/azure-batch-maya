# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import os
from msrest.serialization import Model


class ApplicationTemplateInfo(Model):
    """A reference to an Azure Batch Application Template.

    :param str file_path: The path to an application template file. This can
     be a full path, or relative to the current working directory. Alternatively
     a relative directory can be supplied with the 'current_directory' argument.
     A ValueError will be raised if the supplied file path cannot be found.
    :param dict parameters: A dictory of parameter names and values to be
     subtituted into the application template.
    """

    _validation = {
        'file_path': {'required': True},
    }

    _attribute_map = {
        'file_path': {'key': 'filePath', 'type': 'str'},
        'parameters': {'key': 'parameters', 'type': 'object'},
    }

    def __init__(self, file_path, parameters=None, current_directory="."):
        self.file_path = file_path
        if not os.path.isfile(file_path):
            self.file_path = os.path.abspath(os.path.join(current_directory, str(file_path)))
        self.parameters = parameters

        # Rule: Template file must exist
        # (We do this in order to give a good diagnostic in the most common case, knowing that this is
        # technically a race condition because someone could delete the file between our check here and
        # reading the file later on. We expect such cases to be rare.)
        try:
            with open(self.file_path, 'r'):
                pass
        except EnvironmentError as error:
            raise ValueError("Unable to read the template '{}': {}".format(self.file_path, error))
