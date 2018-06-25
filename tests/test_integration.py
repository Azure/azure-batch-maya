# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import sys
import json
import time
import uuid
import ConfigParser

try:
    from unittest import mock
except ImportError:
    import mock

from environment import BATCH_POOL_IMAGES
import azurebatchutils as utils
from azure.batch_extensions import _file_utils as fileutils

import azure.batch_extensions as batch
from azure.batch_extensions import models
from azure.batch.batch_auth import SharedKeyCredentials
from azure.storage.blob.blockblobservice import BlockBlobService

POOL_ID = "Maya_Pool_766c5218-a5a7-424d-9868-aebb43f98627"  # The OS of the pool will determine whether the job is run with the linux or windows templates.

scriptDir = os.path.dirname(__file__)

cfg = ConfigParser.ConfigParser()
cfg.read(os.path.join(scriptDir, 'data', 'azure_batch_test.ini'))

STORAGE_ACCOUNT = cfg.get('AzureBatch', 'storage_account')
STORAGE_KEY = cfg.get('AzureBatch', 'storage_key')
BATCH_ENDPOINT = cfg.get('AzureBatch', 'batch_url')
BATCH_ACCOUNT = cfg.get('AzureBatch', 'batch_account')
BATCH_KEY = cfg.get('AzureBatch', 'batch_key')

SAMPLE_DIR = os.path.join(scriptDir, 'basic_test_scene')
TEMPLATE_DIR = os.path.abspath('azure_batch_maya/templates')
SCRIPT_DIR = os.path.abspath('azure_batch_maya/scripts/tools')

os.environ['AZUREBATCH_MODULES'] = os.path.abspath('azure_batch_maya/modules')#os.path.join(os.path.split(scriptDir)[0], 'azure_batch_maya/Modules')

def os_flavor(pool_image):
    windows_offers = [value['offer'] for value in BATCH_POOL_IMAGES.values() if 'windows' in value['node_sku_id']]
    linux_offers = [value['offer'] for value in BATCH_POOL_IMAGES.values() if value['offer'] not in windows_offers]
    if pool_image.offer in windows_offers:
        return 'Windows'
    elif pool_image.offer in linux_offers:
        return 'Linux'
    else:
        raise ValueError('Selected pool is not using a valid Maya image.')

def generate_sas_token(storage_client, file_group):
    """Generate SAS token for file group container with read and list
    permissions.
    TODO: Move this into BatchExtensions file utils.
    """
    container_name = fileutils.get_container_name(file_group)
    container_url = fileutils.generate_container_sas_token(
        container_name,
        storage_client,
        permission='rl')
    return container_url


if __name__ == '__main__':
    # Setup client
    storage_client = BlockBlobService(STORAGE_ACCOUNT, STORAGE_KEY, endpoint_suffix="core.windows.net")
    credentials = SharedKeyCredentials(BATCH_ACCOUNT, BATCH_KEY)
    client = batch.BatchExtensionsClient(credentials, base_url=BATCH_ENDPOINT, storage_client=storage_client)

    # Setup test render input data
    scene_file = 'test_scene.mb'
    maya_data = 'maya-data-{}'.format(uuid.uuid4())
    client.file.upload(SAMPLE_DIR, maya_data, flatten=True)
    client.file.upload(os.path.join(SCRIPT_DIR, 'generate_thumbnails.py'), maya_data, flatten=True)

    # Create pool using existing pool template file
    pool_ref = client.pool.get(POOL_ID)
    os_flavor = os_flavor(pool_ref.virtual_machine_configuration.image_reference)
    pool_info = {'poolId': POOL_ID}

    # Create a pool model with an application template reference
    job_id = 'maya_test_{}_{}'.format(os_flavor.lower(), uuid.uuid4())
    batch_parameters = {'id': job_id}
    batch_parameters['displayName'] = "Maya Integration Test using {}".format(os_flavor)
    batch_parameters['metadata'] =  [{"name": "JobType", "value": "Maya"}]
    template_file = os.path.join(TEMPLATE_DIR, 'mayaSoftware-basic-{}.json'.format(os_flavor.lower()))
    batch_parameters['applicationTemplateInfo'] = {'filePath': template_file}
    application_params = {}
    batch_parameters['applicationTemplateInfo']['parameters'] = application_params

    application_params['outputs'] = job_id
    application_params['sceneFile'] = utils.format_scene_path(scene_file, utils.OperatingSystem[os_flavor.lower()])
    application_params['projectData'] = maya_data
    application_params['assetScript'] = client.file.generate_sas_url(maya_data, 'asset_map.mel'.format(os_flavor.lower()))
    application_params['thumbScript'] = client.file.generate_sas_url(maya_data, 'generate_thumbnails.py')
    application_params['workspace'] = client.file.generate_sas_url(maya_data, 'workspace.mel')
    application_params['storageURL'] =  generate_sas_token(storage_client, maya_data)
    application_params['frameStart'] = 1
    application_params['frameEnd'] = 3
    application_params['frameStep'] = 1
    application_params['renderer'] = 'sw'

    batch_parameters['poolInfo'] = pool_info
    new_job = client.job.jobparameter_from_json(batch_parameters)
    client.job.add(new_job)

    # When job is finished, delete it along with input/output file groups
    while True:
        time.sleep(15)
        job = client.job.get(job_id)
        print("Watching job: {}".format(job.state))
        if job.state == models.JobState.completed:
            client.file.download(SAMPLE_DIR, job_id)
            break

    client.job.delete(job_id)
    client.file.delete_group(maya_data)
    client.file.delete_group(job_id)