# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import sys
import traceback

BATCH_MANAGED_IMAGES = {
    'Windows 2016':
    {
            'node_sku_id': 'batch.node.windows amd64',
            'publisher': 'batch',
            'offer': 'rendering-windows2016',
            'sku': 'rendering',
            'version': 'latest'
    },
    'Centos 73':
    {
        'node_sku_id': 'batch.node.centos 7',
        'publisher': 'batch',
        'offer': 'rendering-centos73',
        'sku': 'rendering',
        'version': 'latest'
    },
}

BATCH_MANAGED_IMAGES_WITH_CONTAINERS_JSON = {
    'azurebatchrendering/centos_maya2018update3:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update3',
        'VRay': 'Unsupported',
        'Arnold': 'Unsupported',
        'node_sku_id': 'batch.node.centos 7',
        'ImageReference' : 
        {
            'publisher' : 'microsoft-azure-batch',
            'offer' : 'centos-container',
            'sku' : '7-5',
            'version' : 'latest'
        },
    },
    'azurebatchrendering/centos_maya2018update3_arnold2103:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update3',
        'VRay': 'Unsupported',
        'Arnold': '2.1.0.3',
        'node_sku_id': 'batch.node.centos 7',
        'ImageReference' : 
        {
            'publisher' : 'microsoft-azure-batch',
            'offer' : 'centos-container',
            'sku' : '7-5',
            'version' : 'latest'
        },
    },
    'azurebatchrendering/centos_maya2018update3_vray36004:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update3',
        'VRay': '3.60.04',
        'Arnold': 'Unsupported',
        'node_sku_id': 'batch.node.centos 7',
        'ImageReference' : 
        {
            'publisher' : 'microsoft-azure-batch',
            'offer' : 'centos-container',
            'sku' : '7-5',
            'version' : 'latest'
        },
    },
}

class PoolImageProvider(object):

    #TODO provide read only storage client and load entries from table storage
    def __init__(self, batch_managed_images_with_containers_json = BATCH_MANAGED_IMAGES_WITH_CONTAINERS_JSON):
        self.batchManagedImagesWithContainers = batch_managed_images_with_containers_json

    def getBatchManagedImagesWithContainers(self):
        return self.batchManagedImagesWithContainers
