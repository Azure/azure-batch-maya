# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import ConfigParser
import os
import json
import datetime
import logging
import sys
import traceback
import copy

class PoolImageFilter(object):

    #containerImages should be a dict[string, dictWithFields<OS, Maya, VRay, Arnold, ImageReference>]
    ##TODO containerImages can be static initially, but should be dynamic by reading from Table Storage via a client with read-only access

    #TODO add support for "Any" in dropdown
    def __init__(self, poolImageProvider):

        self.containerImages = poolImageProvider.getContainerImages()

    def getSelectedImage(self, selectedOS, selectedMaya, selectedVRay = None, selectedArnold = None):
        results = copy.deepcopy(self.containerImages)

        results = filterImagesByOS(results, selectedOS)

        results = filterImagesByMaya(results, selectedMaya)
        
        if selectedVRay:
            results = filterImagesByVRayVersion(results, selectedVRay)
        
        if selectedArnold:
            results = filterImagesByArnoldVersion(results, selectedArnold)
        
        image = results[0]
        return image

    def getOSDisplayList(self, currentRenderer = None):
        results = set(i.os for i in self.containerImages)

        if currentRenderer:
             results = filterImagesByRenderer(results, currentRenderer)

        results.discard(None)
        return sorted(results)

    def getMayaDisplayList(self, selectedOS = None, currentRenderer = None):
        results = self.containerImages

        if selectedOS:
            results = filterImagesByOS(results, selectedOS)

        if currentRenderer:
            results = filterImagesByRenderer(results, currentRenderer)

        results = set([i.appVersion for i in results])

        results.discard(None)
        return sorted(results)


    def getVrayDisplayList(self, selectedOS = None, selectedMaya = None):

        results = self.containerImages

        if selectedOS:
            results = filterImagesByOS(results, selectedOS)

        if selectedMaya:
            results = filterImagesByMaya(results, selectedMaya)

        results = set([i.rendererVersion for i in results if i.renderer == "vray"])

        results.discard(None)
        return sorted(results)


    def getArnoldDisplayList(self, selectedOS = None, selectedMaya = None):

        results = self.containerImages

        if selectedOS:
            results = filterImagesByOS(results, selectedOS)

        if selectedMaya:
            results = filterImagesByMaya(results, selectedMaya)

        results = set([i.rendererVersion for i in results if i.renderer == "arnold"])

        results.discard(None)
        return sorted(results)


#private methods
def filterImagesByOS(images, selection):
    imagesFiltered = [i for i in images if i.os == selection]
    return imagesFiltered

def filterImagesByMaya(images, selection):
    imagesFiltered = [i for i in images if i.appVersion == selection]
    return imagesFiltered

def filterImagesByArnoldVersion(images, selection):
    imagesFiltered = [i for i in images if i.renderer == "arnold" and i.rendererVersion == selection]
    return imagesFiltered

def filterImagesByVRayVersion(images, selection):
    imagesFiltered = [i for i in images if i.renderer == "vray" and i.rendererVersion == selection]
    return imagesFiltered

def filterImagesByRenderer(images, selection):
    imagesFiltered = [i for i in images if i.renderer == selection]
    return imagesFiltered
