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

CONTAINER_BASE_IMAGE_REFERENCES = {
    'centos-75-container' :
    {
        'node_sku_id': 'batch.node.centos 7',
        'publisher' : 'microsoft-azure-batch',
        'offer' : 'centos-container',
        'sku' : '7-5',
        'version' : 'latest'
    },
    'ubuntu-1604lts-container' :
    {
        'node_sku_id': 'batch.node.ubuntu 16.04',
        'publisher' : 'microsoft-azure-batch',
        'offer' : 'ubuntu-server-container',
        'sku' : '16-04-lts',
        'version' : 'latest'
    },
    'windowsserver-2016-container' :
    {
        'node_sku_id': 'batch.node.windows amd64',
        'publisher' : 'MicrosoftWindowsServer',
        'offer' : 'WindowsServer',
        'sku' : '2016-DataCenter-With-Containers',
        'version' : 'latest'
    },
}

CONTAINER_IMAGES = {
    'azurebatchrendering/centos_maya2017update5:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2017-Update5',
        'ImageReference' : 'centos-75-container'
    },
    'azurebatchrendering/centos_maya2017update5_arnold2011:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2017-Update5',
        'Arnold': '2.0.1.1',
        'ImageReference' : 'centos-75-container'
    },
    'azurebatchrendering/centos_maya2017update5_arnold3101:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2017-Update5',
        'Arnold': '3.1.0.1',
        'ImageReference' : 'centos-75-container'
    },
    'azurebatchrendering/centos_maya2017update5_vray36004:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2017-Update5',
        'VRay': '3.60.04',
        'ImageReference' : 'centos-75-container'
    },
    'azurebatchrendering/centos_maya2018update2:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update2',
        'ImageReference' : 'centos-75-container'
    },
    'azurebatchrendering/centos_maya2018update2_arnold2023:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update2',
        'Arnold': '2.0.2.3',
        'ImageReference' : 'centos-75-container'
    },
    'azurebatchrendering/centos_maya2018update2_arnold2103:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update2',
        'Arnold': '2.1.0.3',
        'ImageReference' : 'centos-75-container'
    },
    'azurebatchrendering/centos_maya2018update2_arnold3101:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update2',
        'Arnold': '3.1.0.1',
        'ImageReference' : 'centos-75-container'
    },
    'azurebatchrendering/centos_maya2018update2_vray36004:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update2',
        'VRay': '3.60.04',
        'ImageReference' : 'centos-75-container'
    },
    'azurebatchrendering/centos_maya2018update3:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update3',
        'ImageReference' : 'centos-75-container'
    },
    'azurebatchrendering/centos_maya2018update3_arnold2023:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update3',
        'Arnold': '2.0.2.3',
        'ImageReference' : 'centos-75-container'
    },
    'azurebatchrendering/centos_maya2018update3_arnold2103:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update3',
        'Arnold': '2.1.0.3',
        'ImageReference' : 'centos-75-container'
    },
    'azurebatchrendering/centos_maya2018update3_arnold3101:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update3',
        'Arnold': '3.1.0.1',
        'ImageReference' : 'centos-75-container'
    },
    'azurebatchrendering/centos_maya2018update3_vray36004:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update3',
        'VRay': '3.60.04',
        'ImageReference' : 'centos-75-container'
    },
    'azurebatchrendering/centos_maya2018update4:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update4',
        'ImageReference' : 'centos-75-container'
    },
    'azurebatchrendering/centos_maya2018update4_arnold2023:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update4',
        'Arnold': '2.0.2.3',
        'ImageReference' : 'centos-75-container'
    },
    'azurebatchrendering/centos_maya2018update4_arnold2103:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update4',
        'Arnold': '2.1.0.3',
        'ImageReference' : 'centos-75-container'
    },
    'azurebatchrendering/centos_maya2018update4_arnold3101:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update4',
        'Arnold': '3.1.0.1',
        'ImageReference' : 'centos-75-container'
    },
    'azurebatchrendering/centos_maya2018update4_vray36004:latest':
    {
        'OS': 'CentOS 75',
        'Maya': '2018-Update4',
        'VRay': '3.60.04',
        'ImageReference' : 'centos-75-container'
    },
}

class PoolImageProvider(object):

    #TODO provide read only storage client and load entries from table storage
    def __init__(self, base_images = CONTAINER_BASE_IMAGE_REFERENCES, container_images = CONTAINER_IMAGES):
        self.base_images = base_images
        self.container_images = container_images

    def getContainerImages(self):
        merged_images = {}

        for (image_id, image_properties) in self.container_images.items():
            merged_image_properties = {}

            for (property, value) in image_properties.items():
                if property == 'ImageReference':
                    value = self.base_images[value]
                merged_image_properties[property] = value
            merged_images[image_id] = merged_image_properties

        return OrderedDict(sorted(merged_images.items(), key=lambda t: t[0]))

    def getContainerBaseImageReferences(self):
        return OrderedDict(sorted(self.base_images.items(), key=lambda t: t[0]))
