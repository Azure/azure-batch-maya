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

    #containerImages should be a dict[string, dictWithFields<OS, Maya, VRay, Arnold, ImageReference>]
    ##TODO containerImages can be static initially, but should be dynamic by reading from Table Storage via a client with read-only access

    #TODO add support for "Any" in dropdown
    def __init__(self, poolImageProvider):

        self.containerImages = poolImageProvider.getContainerImages()

    def getSelectedImage(self, selectedOS, selectedMaya, selectedVRay = None, selectedArnold = None):
        results = self.containerImages

        results = filterImagesByOS(results, selectedOS)

        results = filterImagesByMaya(results, selectedMaya)
        
        if selectedVRay:
            results = filterImagesByVRay(results, selectedVRay)
        
        if selectedArnold:
            results = filterImagesByArnold(results, selectedArnold)
        
        imageName, image = results.popitem()
        return imageName, image

    def getOSDisplayList(self):
        results = set(i.get("OS") for i in self.containerImages.viewvalues())

        results.discard(None)
        return sorted(results)

    def getMayaDisplayList(self, selectedOS = None):
        results = self.containerImages

        if selectedOS:
            results = filterImagesByOS(results, selectedOS)

        results = set([i.get('Maya') for i in results.viewvalues()])

        results.discard(None)
        return sorted(results)


    def getVrayDisplayList(self, selectedOS = None, selectedMaya = None, selectedArnold = None):

        results = self.containerImages

        if selectedOS:
            results = filterImagesByOS(results, selectedOS)

        if selectedMaya:
            results = filterImagesByMaya(results, selectedMaya)

        if selectedArnold:
            results = filterImagesByArnold(results, selectedArnold)

        results = set([i.get("VRay") for i in results.viewvalues()])

        results.discard(None)
        return sorted(results)


    def getArnoldDisplayList(self, selectedOS = None, selectedMaya = None, selectedVRay = None):

        results = self.containerImages

        if selectedOS:
            results = filterImagesByOS(results, selectedOS)

        if selectedMaya:
            results = filterImagesByMaya(results, selectedMaya)

        if selectedVRay:
            results = filterImagesByVRay(results, selectedVRay)

        results = set([i.get("Arnold") for i in results.viewvalues()])

        results.discard(None)
        return sorted(results)


#private methods
def filterImagesByOS(images, selection):
    imagesFiltered = [i for i in images.viewitems() if i[1].get("OS") == selection]
    return dict(imagesFiltered)

def filterImagesByMaya(images, selection):
    imagesFiltered = [i for i in images.viewitems() if i[1].get("Maya") == selection]
    return dict(imagesFiltered)

def filterImagesByArnold(images, selection):
    imagesFiltered = [i for i in images.viewitems() if i[1].get("Arnold") == selection]
    return dict(imagesFiltered)

def filterImagesByVRay(images, selection):
    imagesFiltered = [i for i in images.viewitems() if i[1].get("VRay") == selection]
    return dict(imagesFiltered)
