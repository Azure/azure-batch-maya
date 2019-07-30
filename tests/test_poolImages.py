# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import os
import sys

from poolImageFilter import PoolImageFilter
from poolImageProvider import PoolImageProvider


class TestPoolImages(unittest.TestCase):

    def setUp(self):
        self.poolImages = PoolImageFilter(PoolImageProvider(image_data_filepath = "../../tests/json_data/rendering-container-images.json"))
        return super(TestPoolImages, self).setUp()

#getOSDisplayList
    def testGetOSDisplayList_IncludesWindowsAndCentos73(self):
        osDisplayList = self.poolImages.getOSDisplayList()

        self.assertEqual(len(osDisplayList), 2)
        self.assertListEqual(osDisplayList, ['CentOS 73', 'WindowsServer2016'])

#getMayaDisplayList
    def testGetMayaDisplayList_Unfiltered_ReturnsCompleteSet(self):
        mayaDisplayList = self.poolImages.getMayaDisplayList()

        self.assertEqual(len(mayaDisplayList), 3)
        self.assertListEqual(mayaDisplayList, ['2017-Update5', '2018-Update1', '2018-Update4'])

    def testGetMayaDisplayList_FilteredByOS_ReturnsFilteredSet(self):
        mayaDisplayList = self.poolImages.getMayaDisplayList(selectedOS = 'WindowsServer2016')

        self.assertEqual(len(mayaDisplayList), 2)
        self.assertListEqual(mayaDisplayList, ['2017-Update5', '2018-Update4'])

    def testGetMayaDisplayList_FilteredByOS_AndRenderer_ReturnsFilteredSet(self):
        mayaDisplayList = self.poolImages.getMayaDisplayList(selectedOS = 'WindowsServer2016', currentRenderer='vray')

        self.assertEqual(len(mayaDisplayList), 1)
        self.assertListEqual(mayaDisplayList, ['2017-Update5'])

#getVRayDisplayList
    def testGetVRayDisplayList_Unfiltered_ReturnsCompleteSet(self):
        vrayDisplayList = self.poolImages.getVrayDisplayList()

        self.assertEqual(len(vrayDisplayList), 4)
        self.assertListEqual(vrayDisplayList, ['1.0.0.1', '1.0.0.2', '1.0.0.4', '3.52.03'])

    def testGetVrayDisplayList_FilteredByOS_ReturnsFilteredSet(self):
        vrayDisplayList = self.poolImages.getVrayDisplayList(selectedOS = 'WindowsServer2016')

        self.assertEqual(len(vrayDisplayList), 1)
        self.assertListEqual(vrayDisplayList, ['1.0.0.1'])

    def testGetVrayDisplayList_FilteredByOS_AndMaya_ReturnsFilteredSet(self):
        vrayDisplayList = self.poolImages.getVrayDisplayList(selectedOS = 'CentOS 73', selectedMaya ='2018-Update1')

        self.assertEqual(len(vrayDisplayList), 1)
        self.assertListEqual(vrayDisplayList, ['3.52.03'])

#getArnoldDisplayList
    def testGetArnoldDisplayList_Unfiltered_ReturnsCompleteSet(self):
        arnoldDisplayList = self.poolImages.getArnoldDisplayList()

        self.assertEqual(len(arnoldDisplayList), 5)
        self.assertListEqual(arnoldDisplayList, ['1.0.0.1', '1.0.0.2', '1.0.0.3', '2.0.1.1', '3.0.0.1'])

    def testGetArnoldDisplayList_FilteredByOS_ReturnsFilteredSet(self):
        arnoldDisplayList = self.poolImages.getArnoldDisplayList(selectedOS = 'WindowsServer2016')

        self.assertEqual(len(arnoldDisplayList), 2)
        self.assertListEqual(arnoldDisplayList, ['1.0.0.3', '3.0.0.1'])

    def testGetArnoldDisplayList_FilteredByOS_AndMaya_ReturnsFilteredSet(self):
        arnoldDisplayList = self.poolImages.getArnoldDisplayList(selectedOS = 'CentOS 73', selectedMaya ='2018-Update1')

        self.assertEqual(len(arnoldDisplayList), 1)
        self.assertListEqual(arnoldDisplayList, ['2.0.1.1'])

#getSelectedImage
    def testGetSelectedImage_OSMayaOnly_ReturnsFirstValidEntry(self):
        selectedImage = self.poolImages.getSelectedImage(selectedOS = 'CentOS 73', selectedMaya = '2017-Update5')
        self.assertEqual(selectedImage.os, 'CentOS 73')

    def testGetSelectedImage_OSMayaVRay_ReturnsFirstValidEntry(self):
        selectedImage = self.poolImages.getSelectedImage(selectedOS = 'CentOS 73', selectedMaya = '2017-Update5', selectedVRay = '1.0.0.2')
        self.assertEqual(selectedImage.os, 'CentOS 73')

    def testGetSelectedImage_OSMayaArnold_ReturnsFirstValidEntry(self):
        selectedImage = self.poolImages.getSelectedImage(selectedOS = 'CentOS 73', selectedMaya = '2017-Update5', selectedArnold = '1.0.0.1')
        self.assertEqual(selectedImage.os, 'CentOS 73')
    
