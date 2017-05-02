# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

# Not ideal syntax - but savaes us having to check and repopulate this
# list every time the SDK is regenerated.
from azure.batch.models import *
from azure.batch.models.batch_service_client_enums import *

from .extended_task_parameter import ExtendedTaskParameter
from .extended_job_parameter import ExtendedJobParameter
from .extended_pool_parameter import ExtendedPoolParameter
from .extended_pool_specification import ExtendedPoolSpecification
from .auto_pool_specification import AutoPoolSpecification
from .output_file import OutputFile
from .extended_output_file_destination import ExtendedOutputFileDestination
from .output_file_auto_storage_destination import OutputFileAutoStorageDestination
from .extended_resource_file import ExtendedResourceFile
from .file_source import FileSource
from .task_factory_base import TaskFactoryBase
from .task_collection_task_factory import TaskCollectionTaskFactory
from .parametric_sweep_task_factory import ParametricSweepTaskFactory
from .file_collection_task_factory import FileCollectionTaskFactory
from .parameter_set import ParameterSet
from .repeat_task import RepeatTask
from .package_reference_base import PackageReferenceBase
from .chocolatey_package_reference import ChocolateyPackageReference
from .yum_package_reference import YumPackageReference
from .apt_package_reference import AptPackageReference
from .application_template_info import ApplicationTemplateInfo
from .merge_task import MergeTask
from .job_preparation_task import JobPreparationTask
from .job_release_task import JobReleaseTask
from .job_manager_task import JobManagerTask
from .start_task import StartTask
from .application_template import ApplicationTemplate


from .constants import (
    PROPS_RESERVED_FOR_JOBS,
    PROPS_PERMITTED_ON_TEMPLATES,
    ROOT_FILE_UPLOAD_URL,
    FILE_EGRESS_OVERRIDE,
    FILE_EGRESS_ENV_NAME,
    FILE_EGRESS_PREFIX,
    FILE_EGRESS_RESOURCES)
