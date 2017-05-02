# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------


ROOT_FILE_UPLOAD_URL = 'https://raw.githubusercontent.com/Azure/azure-batch-cli-extensions/master'
FILE_EGRESS_OVERRIDE = 'FILE_EGRESS_OVERRIDE_URL'
FILE_EGRESS_ENV_NAME = 'AZ_BATCH_FILE_UPLOAD_CONFIG'
FILE_EGRESS_PREFIX = 'azure/cli/command_modules/batch_extensions/fileegress/'
FILE_EGRESS_RESOURCES = {
    FILE_EGRESS_PREFIX + 'batchfileuploader.py',
    FILE_EGRESS_PREFIX + 'configuration.py',
    FILE_EGRESS_PREFIX + 'requirements.txt',
    FILE_EGRESS_PREFIX + 'setup_uploader.py',
    FILE_EGRESS_PREFIX + 'uploader.py',
    FILE_EGRESS_PREFIX + 'util.py',
    FILE_EGRESS_PREFIX + 'uploadfiles.py'}


# These properties are reserved for application template use
# and may not be used on jobs using an application template
PROPS_RESERVED_FOR_TEMPLATES = {
    'jobManagerTask',
    'jobPreparationTask',
    'jobReleaseTask',
    'commonEnvironmentSettings',
    'usesTaskDependencies',
    'onAllTasksComplete',
    'onTaskFailure',
    'taskFactory'}


PROPS_PERMITTED_ON_TEMPLATES = PROPS_RESERVED_FOR_TEMPLATES.union({
    'templateMetadata',
    'parameters',
    'metadata'})


ATTRS_RESERVED_FOR_TEMPLATES = {
    'job_manager_task',
    'job_preparation_task',
    'job_release_task',
    'common_environment_settings',
    'uses_task_dependencies',
    'on_all_tasks_complete',
    'on_task_failure',
    'task_factory'}


# These properties are reserved for job use
# and may not be used on an application template
PROPS_RESERVED_FOR_JOBS = {
    'id',
    'displayName',
    'priority',
    'constraints',
    'poolInfo',
    'applicationTemplateInfo'}


# Properties on a repeatTask object that should be
# applied to each expanded task.
PROPS_ON_REPEAT_TASK = {
    'displayName',
    'resourceFiles',
    'environmentSettings',
    'constraints',
    'userIdentity',
    'exitConditions',
    'clientExtensions',
    'outputFiles',
    'packageReferences'}


PROPS_ON_COLLECTION_TASK = PROPS_ON_REPEAT_TASK.union({
    'multiInstanceSettings',
    'dependsOn'})
