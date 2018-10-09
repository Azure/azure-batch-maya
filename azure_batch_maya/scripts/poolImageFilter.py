# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import ConfigParser
import os
import json
import datetime
import dateutil.tz
import logging
import sys
import traceback
import adal

class PoolImageFilter(object):

    #batchManagedImagesWithContainers should be a dict[string, dictWithFields<OS, Maya, VRay, Arnold, ImageReference>]
    ##TODO batchManagedImagesWithContainers can be static initially, but should be dynamic by reading from Table Storage via a client with read-only access
    

    #TODO add support for "Any" in dropdown
    def __init__(self, poolImageProvider):

        self.batchManagedImagesWithContainers = poolImageProvider.getBatchManagedImagesWithContainers()

    def getSelectedImage(self, selectedOS, selectedMaya, selectedVRay = None, selectedArnold = None):
        results = self.batchManagedImagesWithContainers

        results = filterImagesByOS(results, selectedOS)

        results = filterImagesByMaya(results, selectedMaya)
        
        if selectedVRay:
            results = filterImagesByVRay(results, selectedVRay)
        
        if selectedArnold:
            results = filterImagesByArnold(results, selectedArnold)
        
        imageName, image = results.popitem()
        return imageName, image

    def getOSDisplayList(self):

        results = set(i["OS"] for i in self.batchManagedImagesWithContainers.viewvalues())

        return results

    def getMayaDisplayList(self, selectedOS = None):
        results = self.batchManagedImagesWithContainers

        if selectedOS:
            results = filterImagesByOS(results, selectedOS)

        resultset = set([i['Maya'] for i in results.viewvalues()])
        resultset.discard('Unsupported')
        return resultset


    def getVrayDisplayList(self, selectedOS = None, selectedMaya = None, selectedArnold = None):

        results = self.batchManagedImagesWithContainers

        if selectedOS:
            results = filterImagesByOS(results, selectedOS)

        if selectedMaya:
            results = filterImagesByMaya(results, selectedMaya)

        if selectedArnold:
            results = filterImagesByArnold(results, selectedArnold)

        resultset = set([i["VRay"] for i in results.viewvalues()])
        resultset.discard('Unsupported')
        return resultset


    def getArnoldDisplayList(self, selectedOS = None, selectedMaya = None, selectedVRay = None):

        results = self.batchManagedImagesWithContainers

        if selectedOS:
            results = filterImagesByOS(results, selectedOS)

        if selectedMaya:
            results = filterImagesByMaya(results, selectedMaya)

        if selectedVRay:
            results = filterImagesByVRay(results, selectedVRay)

        resultset = set([i["Arnold"] for i in results.viewvalues()])
        resultset.discard('Unsupported')
        return resultset

#private methods
def filterImagesByOS(images, selection):
    imagesFiltered = [i for i in images.viewitems() if i[1]["OS"] == selection]
    return dict(imagesFiltered)

def filterImagesByMaya(images, selection):
    imagesFiltered = [i for i in images.viewitems() if i[1]["Maya"] == selection]
    return dict(imagesFiltered)

def filterImagesByArnold(images, selection):
    imagesFiltered = [i for i in images.viewitems() if i[1]["Arnold"] == selection]
    return dict(imagesFiltered)

def filterImagesByVRay(images, selection):
    imagesFiltered = [i for i in images.viewitems() if i[1]["VRay"] == selection]
    return dict(imagesFiltered)
