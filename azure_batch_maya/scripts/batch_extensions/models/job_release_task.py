# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from msrest.serialization import Model


class JobReleaseTask(Model):
    """A Job Release task to run on job completion on any compute node where the
    job has run.

    :param id: A string that uniquely identifies the Job Release task within
     the job. The ID can contain any combination of alphanumeric characters
     including hyphens and underscores and cannot contain more than 64
     characters. If you do not specify this property, the Batch service assigns
     a default value of 'jobrelease'. No other task in the job can have the
     same id as the Job Release task. If you try to submit a task with the same
     id, the Batch service rejects the request with error code
     TaskIdSameAsJobReleaseTask; if you are calling the REST API directly, the
     HTTP status code is 409 (Conflict).
    :type id: str
    :param command_line: The command line of the Job Release task. The command
     line does not run under a shell, and therefore cannot take advantage of
     shell features such as environment variable expansion. If you want to take
     advantage of such features, you should invoke the shell in the command
     line, for example using "cmd /c MyCommand" in Windows or "/bin/sh -c
     MyCommand" in Linux.
    :type command_line: str
    :param resource_files: A list of files that the Batch service will
     download to the compute node before running the command line. Files listed
     under this element are located in the task's working directory.
    :type resource_files: list of :class:`ExtendedResourceFile
     <azure.batch_extensions.models.ExtendedResourceFile>`
    :param environment_settings: A list of environment variable settings for
     the Job Release task.
    :type environment_settings: list of :class:`EnvironmentSetting
     <azure.batch.models.EnvironmentSetting>`
    :param max_wall_clock_time: The maximum elapsed time that the Job Release
     task may run on a given compute node, measured from the time the task
     starts. If the task does not complete within the time limit, the Batch
     service terminates it. The default value is 15 minutes. You may not
     specify a timeout longer than 15 minutes. If you do, the Batch service
     rejects it with an error; if you are calling the REST API directly, the
     HTTP status code is 400 (Bad Request).
    :type max_wall_clock_time: timedelta
    :param retention_time: The minimum time to retain the task directory for
     the Job Release task on the compute node. After this time, the Batch
     service may delete the task directory and all its contents. The default is
     infinite, i.e. the task directory will be retained until the compute node
     is removed or reimaged.
    :type retention_time: timedelta
    :param user_identity: The user identity under which the Job Release task
     runs. If omitted, the task runs as a non-administrative user unique to the
     task.
    :type user_identity: :class:`UserIdentity
     <azure.batch.models.UserIdentity>`
    """

    _validation = {
        'command_line': {'required': True},
    }

    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'command_line': {'key': 'commandLine', 'type': 'str'},
        'resource_files': {'key': 'resourceFiles', 'type': '[ExtendedResourceFile]'},
        'environment_settings': {'key': 'environmentSettings', 'type': '[EnvironmentSetting]'},
        'max_wall_clock_time': {'key': 'maxWallClockTime', 'type': 'duration'},
        'retention_time': {'key': 'retentionTime', 'type': 'duration'},
        'user_identity': {'key': 'userIdentity', 'type': 'UserIdentity'},
    }

    def __init__(self, command_line, id=None, resource_files=None, environment_settings=None, max_wall_clock_time=None, retention_time=None, user_identity=None):
        self.id = id
        self.command_line = command_line
        self.resource_files = resource_files
        self.environment_settings = environment_settings
        self.max_wall_clock_time = max_wall_clock_time
        self.retention_time = retention_time
        self.user_identity = user_identity
