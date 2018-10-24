# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import sys
import traceback

MARKETPLACE_IMAGES = {
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

CONTAINER_IMAGES = {
    'azurebatchrendering/centos_maya2018update3:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update3',
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
        'node_sku_id': 'batch.node.centos 7',
        'ImageReference' : 
        {
            'publisher' : 'microsoft-azure-batch',
            'offer' : 'centos-container',
            'sku' : '7-5',
            'version' : 'latest'
        },
    },
    'azurebatchrendering/centos_maya2018update4:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update4',
        'node_sku_id': 'batch.node.centos 7',
        'ImageReference' : 
        {
            'publisher' : 'microsoft-azure-batch',
            'offer' : 'centos-container',
            'sku' : '7-5',
            'version' : 'latest'
        },
    },
    'azurebatchrendering/centos_maya2018update4_arnold3101:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update4',
        'Arnold': '3.1.0.1',
        'node_sku_id': 'batch.node.centos 7',
        'ImageReference' : 
        {
            'publisher' : 'microsoft-azure-batch',
            'offer' : 'centos-container',
            'sku' : '7-5',
            'version' : 'latest'
        },
    },
    'azurebatchrendering/centos_maya2018update4_vray36004:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update4',
        'VRay': '3.60.04',
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
    def __init__(self, container_images = CONTAINER_IMAGES):
        self.container_images = container_images

    def getContainerImages(self):
        return self.container_images
