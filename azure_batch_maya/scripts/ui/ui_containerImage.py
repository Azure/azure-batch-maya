# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# -------------------------------------------------------------------------------------------- 

import azurebatchutils as utils

from enum import Enum
from azurebatchmayaapi import MayaAPI as maya

class ContainerImageUI(object):

    def __init__(self, poolImageFilter, parent, image_config, renderer, local_maya_version):

        self.poolImageFilter = poolImageFilter

        self.renderer = renderer

        self.selected_os = None
        self.selected_maya = None
        self.selected_vray = None
        self.selected_arnold = None

        self.maya_dropdown = None
        
        with utils.FrameLayout(
            label="Container Image Settings", collapsable=True,
            width=325, collapse=False, parent = parent) as framelayout:

            image_config.append(framelayout)
            initial_maya_version = "" 

            with utils.ColumnLayout(
                2, col_width=((1,100),(2,200)), row_spacing=(1,5),
                row_offset=((1, "top", 15),(5, "bottom", 15)), parent=framelayout) as imageLayout:  

                image_config.append(imageLayout)

                image_config.append(maya.text(label="OS : ", align='left', parent=imageLayout))

                with utils.Dropdown(self.os_dropdown_set, parent=imageLayout) as os_dropdown:

                    image_config.append(os_dropdown)

                    self.os_dropdown = os_dropdown

                    for os_version in self.poolImageFilter.getOSDisplayList():
                        self.os_dropdown.add_item(os_version)
                    
                    self.selected_os = self.os_dropdown.value()

                image_config.append(maya.text(label="Maya Version : ", align='left', parent=imageLayout))

                with utils.Dropdown(self.maya_dropdown_set, parent=imageLayout) as maya_dropdown:

                    image_config.append(maya_dropdown)
                    self.maya_dropdown = maya_dropdown  

                    for maya_version in self.poolImageFilter.getMayaDisplayList(self.selected_os):
                        self.maya_dropdown.add_item(maya_version)
                        #store the last version returned which is for the same year as the locally running Maya, e.g. 2019
                        if maya_version.startswith(local_maya_version):
                            initial_maya_version = maya_version

                if self.renderer == "vray":

                    image_config.append(maya.text(label="VRay Version : ", align='left', parent=imageLayout))

                    with utils.Dropdown(self.vray_dropdown_set, parent = imageLayout) as vray_dropdown:
                        image_config.append(vray_dropdown)
                        self.vray_dropdown = vray_dropdown 
                        for vray_version in self.poolImageFilter.getVrayDisplayList(self.selected_os, self.selected_maya):
                            self.vray_dropdown.add_item(vray_version)

                        self.selected_vray = self.vray_dropdown.value()

                if self.renderer == "arnold":

                    image_config.append(maya.text(label="Arnold Version : ", align='left', parent=imageLayout))

                    with utils.Dropdown(self.arnold_dropdown_set, parent = imageLayout) as arnold_dropdown:
                        image_config.append(arnold_dropdown)
                        self.arnold_dropdown = arnold_dropdown 
                        for arnold_version in self.poolImageFilter.getArnoldDisplayList(self.selected_os, self.selected_maya):
                            self.arnold_dropdown.add_item(arnold_version)

                        self.selected_arnold = self.arnold_dropdown.value()
        
        self.maya_dropdown.select(initial_maya_version)

    def os_dropdown_set(self, selected_os):
        self.selected_os = selected_os

        self.maya_dropdown.clear()
        for version in self.poolImageFilter.getMayaDisplayList(selected_os):
            self.maya_dropdown.add_item(version)
        self.selected_maya = self.maya_dropdown.value()
            
        if self.renderer == "vray":
            self.vray_dropdown.clear()
            for version in self.poolImageFilter.getVrayDisplayList(selected_os):
                self.vray_dropdown.add_item(version)
            self.selected_vray = self.vray_dropdown.value()

        if self.renderer == "arnold":
            self.arnold_dropdown.clear()
            for version in self.poolImageFilter.getArnoldDisplayList(selected_os):
                self.arnold_dropdown.add_item(version)
            self.selected_arnold = self.arnold_dropdown.value()
        
    def maya_dropdown_set(self, selected_maya):
        self.selected_maya = selected_maya
        
        if self.renderer == "vray":
            self.vray_dropdown.clear()
            for version in self.poolImageFilter.getVrayDisplayList(self.selected_os, selected_maya):
                self.vray_dropdown.add_item(version)
            self.selected_vray = self.vray_dropdown.value()

        if self.renderer == "arnold":
            self.arnold_dropdown.clear()
            for version in self.poolImageFilter.getArnoldDisplayList(self.selected_os, selected_maya):
                self.arnold_dropdown.add_item(version)
            self.selected_arnold = self.arnold_dropdown.value()

    def vray_dropdown_set(self, selected_vray):
        self.selected_vray = selected_vray

    def arnold_dropdown_set(self, selected_arnold):
        self.selected_arnold = selected_arnold

    def fetch_selected_image(self):
        return self.poolImageFilter.getSelectedImage(self.selected_os, self.selected_maya, self.selected_vray, self.selected_arnold)

    def selected_image_node_sku_id(self):
        selectedImage = self.fetch_selected_image()
        return selectedImage.imageReference.node_sku_id

    def selected_image_image_reference(self):
        selectedImage = self.fetch_selected_image()
        return selectedImage.imageReference
