# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import sys
import traceback

from collections import OrderedDict

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
    'azurebatchrendering/centos_maya2017update5:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2017-Update5',
        'node_sku_id': 'batch.node.centos 7',
        'ImageReference' : 
        {
            'publisher' : 'microsoft-azure-batch',
            'offer' : 'centos-container',
            'sku' : '7-5',
            'version' : 'latest'
        },
    },
    'azurebatchrendering/centos_maya2017update5_arnold2011:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2017-Update5',
        'Arnold': '2.0.1.1',
        'node_sku_id': 'batch.node.centos 7',
        'ImageReference' : 
        {
            'publisher' : 'microsoft-azure-batch',
            'offer' : 'centos-container',
            'sku' : '7-5',
            'version' : 'latest'
        },
    },
    'azurebatchrendering/centos_maya2017update5_arnold3101:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2017-Update5',
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
    'azurebatchrendering/centos_maya2017update5_vray36004:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2017-Update5',
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
    'azurebatchrendering/centos_maya2018update2:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update2',
        'node_sku_id': 'batch.node.centos 7',
        'ImageReference' : 
        {
            'publisher' : 'microsoft-azure-batch',
            'offer' : 'centos-container',
            'sku' : '7-5',
            'version' : 'latest'
        },
    },
    'azurebatchrendering/centos_maya2018update2_arnold2023:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update2',
        'Arnold': '2.0.2.3',
        'node_sku_id': 'batch.node.centos 7',
        'ImageReference' : 
        {
            'publisher' : 'microsoft-azure-batch',
            'offer' : 'centos-container',
            'sku' : '7-5',
            'version' : 'latest'
        },
    },
    'azurebatchrendering/centos_maya2018update2_arnold2103:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update2',
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
    'azurebatchrendering/centos_maya2018update2_arnold3101:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update2',
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
    'azurebatchrendering/centos_maya2018update2_vray36004:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update2',
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
    'azurebatchrendering/centos_maya2018update3_arnold2023:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update3',
        'Arnold': '2.0.2.3',
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
    'azurebatchrendering/centos_maya2018update3_arnold3101:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update3',
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
    'azurebatchrendering/centos_maya2018update4_arnold2023:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update4',
        'Arnold': '2.0.2.3',
        'node_sku_id': 'batch.node.centos 7',
        'ImageReference' : 
        {
            'publisher' : 'microsoft-azure-batch',
            'offer' : 'centos-container',
            'sku' : '7-5',
            'version' : 'latest'
        },
    },
    'azurebatchrendering/centos_maya2018update4_arnold2103:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update4',
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
        return OrderedDict(sorted(self.container_images.items(), key=lambda t: t[0]))
