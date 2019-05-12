# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import sys
import traceback
import os

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

class ImageReference(object):

    def __init__(self, id, node_sku_id, publisher, offer, sku, version):
        self.id = id
        self.node_sku_id = node_sku_id
        self.publisher = publisher
        self.offer = offer
        self.sku = sku
        self.version = version

class ContainerImage(object):

    def __init__(self, containerImage, os, appVersion, renderer, rendererVersion, imageReference):
        self.containerImage = containerImage
        self.os = os
        self.appVersion = appVersion
        self.renderer = renderer
        self.rendererVersion = rendererVersion
        self.imageReference = imageReference

class PoolImageProvider(object):

    def __init__(self, image_data_filepath = "tools/rendering-container-images.json"):
        current_file_dir = os.path.dirname(__file__)
        relative_filepath = os.path.join(current_file_dir, image_data_filepath)

        with open(relative_filepath) as images_json_file:
            containerImageJson = json.load(images_json_file)
            self.base_images = []
            self.container_images = []
            for imageReference in containerImageJson["imageReferences"]:
                self.base_images.append(ImageReference(
                    imageReference["id"], 
                    imageReference["node_sku_id"], 
                    imageReference["publisher"],
                    imageReference["offer"],
                    imageReference["sku"],
                    imageReference["version"]))

            for containerImage in containerImageJson["containerImages"]:
                image_reference = [baseImage for baseImage in self.base_images if baseImage.id == containerImage["imageReferenceId"]][0]
                if containerImage["app"] == "maya":
                    self.container_images.append(ContainerImage(
                        containerImage["containerImage"], 
                        containerImage["os"], 
                        containerImage["appVersion"], 
                        containerImage["renderer"], 
                        containerImage["rendererVersion"], 
                        image_reference))

    def getContainerImages(self):
        return sorted(self.container_images, key=lambda t: t.containerImage)

    def getContainerBaseImageReferences(self):
        return sorted(self.base_images, key=lambda t: t.id)
