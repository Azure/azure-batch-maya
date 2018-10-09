# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import azurebatchutils as utils

from enum import Enum
from azurebatchmayaapi import MayaAPI as maya

from ui_batchManagedImageWithContainers import BatchManagedImageWithContainersUI
from poolImageProvider import PoolImageProvider
from poolImageFilter import PoolImageFilter

def edit_cell(*args):
    return 1

class PoolImageMode(Enum):
    BATCH_IMAGE = 1
    BATCH_IMAGE_WITH_CONTAINERS = 2
    CUSTOM_IMAGE = 3
    CUSTOM_IMAGE_WITH_CONTAINERS = 4

class EnvironmentUI(object):
    """Class to create the 'Env' tab in the plug-in UI"""

    def __init__(self, base, frame, images, skus, licenses):
        """Create 'Env' tab and add to UI frame.

        :param base: The base class for handling Maya and plugin-related functionality.
        :type base: :class:`.AzureBatchEnvironment`
        :param frame: The shared plug-in UI frame.
        :type frame: :class:`.AzureBatchUI`
        """
        self.base = base
        self.label = " Env  "
        self.ready = False
        self.page = maya.form_layout(enableBackground=True)
        self.license_settings = {}
        self.select_rendernode_type = PoolImageMode.BATCH_IMAGE.value
        self.poolImageFilter = PoolImageFilter(PoolImageProvider())
        self.batchManagedImageWithContainersUI = None
        self.licenses = licenses
        self.image_arm_id = ""
        self.node_sku_id = ""
        self.container_registry_server = ""
        self.container_registry_username = ""
        self.container_registry_password = ""
        self.container_image = ""
        self.batch_images = images

        with utils.ScrollLayout(
            v_scrollbar=3, h_scrollbar=0, height=520) as scroll:

            with utils.RowLayout(row_spacing=20) as sublayout:
                with utils.FrameLayout(
                    label="Render Node Configuration", collapsable=True, width=325, collapse=False) as rendernode_config:
                    self.rendernode_config = rendernode_config
                    with utils.ColumnLayout(
                        2, col_width=((1,80),(2,160)), row_spacing=(1,5),
                        row_offset=((1, "top", 15),(5, "bottom", 15))):
                        maya.text(label="Use VM SKU: ", align='left')
                        with utils.Dropdown(self.set_sku) as sku_settings:
                            self._sku = sku_settings
                            for sku in skus:
                                self._sku.add_item(sku)

                    with utils.Row(1,1,325):
                        maya.radio_group(
                            labelArray2=("Batch Managed Image",
                                         "Batch Managed Image with Containers"),
                            numberOfRadioButtons=2,
                            select=self.select_rendernode_type,
                            vertical = True,
                            onCommand1=self.set_batch_image,
                            onCommand2=self.set_batch_image_with_containers)

                    maya.parent()
                    self.image_config = []
                    with utils.FrameLayout(
                        label="Batch Managed Image Settings", collapsable=True,
                        width=325, collapse=False, parent = self.rendernode_config) as framelayout:
                        self.image_config.append(framelayout)
                        with utils.ColumnLayout(
                            2, col_width=((1,160),(2,160)), row_spacing=(1,5),
                            row_offset=((1, "top", 15),(5, "bottom", 15)), parent=framelayout) as os_image_layout:
                            self.image_config.append(os_image_layout)
                            maya.text(label="Use Image: ", align='right', parent=os_image_layout)
                            with utils.Dropdown(self.set_os_image, parent=os_image_layout) as image_settings:
                                self._image = image_settings
                                for image in self.batch_images:
                                    self._image.add_item(image)

                with utils.FrameLayout(
                    label="Environment Variables", collapsable=True,
                    width=325, collapse=True):
                    
                    with utils.Row(1,1,325):
                        self.env_vars = maya.table(height=120,
                            rows=0, columns=2, columnWidth=[(1,155), (2,155)],
                            label=[(1,"Setting"), (2,"Value")], rowHeight=15,
                            editable=False, selectionBehavior=1,
                            getCellCmd=self.populate_row)

                    with utils.ColumnLayout(2, col_width=((1,160),(2,160))):
                        self.custom_env_var = maya.text_field(
                            placeholderText='Env Variable' )
                        self.custom_env_val = maya.text_field(
                            placeholderText='Value' )
                        maya.button(
                            label="Add", command=self.add_row)
                        maya.button(
                            label="Delete", command=self.delete_row)

        with utils.Row(1, 1, 355, "center", (1,"bottom",0)) as btn:
            self.refresh_button = utils.ProcButton(
                "Refresh", "Refreshing...", self.refresh)
        maya.form_layout(self.page, edit=True, 
                         attachForm=[(scroll, 'top', 5), (scroll, 'left', 5),
                                     (scroll, 'right', 5), (btn, 'bottom', 5),
                                     (btn, 'left', 5), (btn, 'right', 5)],
                         attachControl=(scroll, "bottom", 5, btn))
        frame.add_tab(self)
        self.is_logged_out()

    def delete_row(self, *args):
        """Remove selected row from user environment variables table."""
        selected_row = maya.table(self.env_vars, query=True, selectedRow=True)
        maya.table(self.env_vars, edit=True, deleteRow=selected_row)

    def add_row(self, *args):
        """Add new user environment variable from contents of custom_env text
        fields.
        """
        env_var = maya.text_field(self.custom_env_var, query=True, text=True)
        env_val = maya.text_field(self.custom_env_val, query=True, text=True)
        if env_var and env_val:
            maya.table(self.env_vars, edit=True, insertRow=1)

    def populate_row(self, row, column):
        """Add data to table cell. Command called by table getCell automatically
        when new row is added.
        :param int row: Selected row index.
        :param int column: Selected column index.
        """
        if column == 1:
            env_var = maya.text_field(
                self.custom_env_var, query=True, text=True)
            maya.text_field(self.custom_env_var, edit=True, text="")
            return env_var

        if column == 2:
            env_val = maya.text_field(
                self.custom_env_val, query=True, text=True)
            maya.text_field(self.custom_env_val, edit=True, text="")
            return env_val

    def set_os_image(self, image):
        """Set VM image to run on the render node. Command for image dropdown
        selection. This value will be stored in the config file.
        :param str image: The selected image name, e.g. 'Batch Windows Preview'.
        """
        self.base.batch_image = image

    def get_os_image(self):
        """Retrieve the currently selected image name."""
        if self.select_rendernode_type == PoolImageMode.BATCH_IMAGE.value:
            return self._image.value()
        return self.get_custom_image_resource_id()

    def get_image_type(self):
        """Retrieve the currently selected image type."""
        return PoolImageMode(self.select_rendernode_type)

    def select_image(self, image):
        """Select the cached image value if available."""
        # TODO: Check value against current lists. 
        if image:
            self._image.select(image)

    def set_sku(self, sku):
        """Set the VM SKU to use for the render nodes. Command for SKU dropdown
        selection. This value will be stored in the config file.
        :param str sku: The selected hardware SKU.
        """
        self.base.vm_sku = sku

    def get_sku(self):
        """Retrieve the currently selected VM SKU."""
        return self._sku.value()

    def select_sku(self, sku):
        """Selected the cached SKU value if available."""
        # TODO: Validate against SKU list.
        if sku:
            self._sku.select(sku)

    def select_node_sku_id(self, node_sku_id):
        if node_sku_id:
            #if the dropdown hasn't been created yet (because "Custom Image" hasn't been selected) store value in a temporary value
            if not self._node_sku_id_dropdown:
                self.node_sku_id = node_sku_id
            else:
                self._node_sku_id_dropdown.select(node_sku_id)

    def get_custom_image_arm_id(self):
        return maya.text_field(self.image_arm_id_field, query=True, text=True)

    def set_node_sku_id(self, node_sku_id):
        self.base.set_node_sku_id(node_sku_id)

    def get_node_sku_id(self):
        if self.get_image_type().value == PoolImageMode.BATCH_IMAGE.value:
            image = self.base.get_batch_image()
            return image.pop('node_sku_id')
        if self.get_image_type().value == PoolImageMode.BATCH_IMAGE_WITH_CONTAINERS.value:
            return self.batchManagedImageWithContainersUI.selected_image_node_sku_id()
        if not self._node_sku_id_dropdown:
            return self.base.node_sku_id
        return self._node_sku_id_dropdown.value()

    def get_custom_image_resource_id(self):
        value_in_text_field = maya.text_field(self.image_resource_id_field, query=True, text=True)
        if value_in_text_field == None:
            return self.custom_image_resource_id
        return value_in_text_field

    def select_custom_image_resource_id(self, custom_image_resource_id):
        if custom_image_resource_id:
             self.custom_image_resource_id = custom_image_resource_id

    def set_custom_image_resource_id(self, custom_image_resource_id):
        self.base.set_custom_image_resource_id(custom_image_resource_id)

    def get_task_container_image(self):
        if self.select_rendernode_type == PoolImageMode.BATCH_IMAGE_WITH_CONTAINERS.value:
            selectedImageId, selectedImage = self.batchManagedImageWithContainersUI.fetch_selected_image()
            return selectedImageId
        return None

    def get_pool_container_images(self):
        if self.select_rendernode_type == PoolImageMode.BATCH_IMAGE_WITH_CONTAINERS.value:
            selectedImageId, selectedImage = self.batchManagedImageWithContainersUI.fetch_selected_image()
            return [selectedImageId]
        return []
        
    def get_container_image_reference(self):
        if self.select_rendernode_type == PoolImageMode.BATCH_IMAGE_WITH_CONTAINERS.value:
             return self.batchManagedImageWithContainersUI.selected_image_image_reference()
        return None

    def get_env_vars(self):
        """Retrieve all user environment variables.
        :returns: Environment variables as a dictionary.
        """
        vars = {}
        rows = maya.table(self.env_vars, query=True, rows=True)
        for row in range(1, rows):
            row_key = maya.table(
                self.env_vars, cellIndex=(row, 1), query=True, cellValue=True)
            row_val = maya.table(
                self.env_vars, cellIndex=(row, 2), query=True, cellValue=True)
            vars[row_key[0]] = row_val[0]
        return vars

    def refresh(self, *args):
        """Clear any data and customization. Command for refresh_button."""
        maya.table(self.env_vars, edit=True, clearTable=True, rows=0)
        self.base.refresh()
        if self.select_rendernode_type == PoolImageMode.BATCH_IMAGE_WITH_CONTAINERS.value:
            self.set_batch_image_with_containers()
        maya.refresh()

    def is_logged_in(self):
        """Called when the plug-in is authenticated. Enables UI."""
        maya.form_layout(self.page, edit=True, enable=True)

    def is_logged_out(self):
        """Called when the plug-in is logged out. Disables UI and resets
        whether that tab has been loaded for the first time.
        """
        maya.form_layout(self.page, edit=True, enable=False)
        self.ready = False

    def prepare(self):
        """Called when the tab is loaded (clicked into) for the first time.
        Once loaded, remains so for the rest of the plug-in session unless
        logged out or manually refreshed.
        If loading the UI fails, the tab returns to a logged-out state.
        """
        if not self.ready:
            maya.refresh()
            try:
                self.is_logged_in()
                self.ready = True
            except Exception as exp:
                maya.error("Error starting Environment UI: {0}".format(exp))
                self.is_logged_out()
        maya.refresh()

    def set_batch_image(self, *args):
        """Set selected render node type to be a batch published VM image type.
        Displays the Batch VM image selection UI control.
        Command for select_rendernode_type radio buttons.
        """
        self.select_rendernode_type = PoolImageMode.BATCH_IMAGE.value
        maya.delete_ui(self.image_config)
        self.image_config = []
        with utils.FrameLayout(
            label="Batch Managed Image Settings", collapsable=True,
            width=325, collapse=False, parent = self.rendernode_config) as framelayout:
            self.image_config.append(framelayout)
            with utils.ColumnLayout(
                2, col_width=((1,80),(2,160)), row_spacing=(1,5),
                row_offset=((1, "top", 15),(5, "bottom", 15)), parent=framelayout) as os_image_layout:  
                self.image_config.append(os_image_layout)
                maya.text(label="Use Image: ", align='left', parent=os_image_layout)
                with utils.Dropdown(self.set_os_image, parent=os_image_layout) as image_settings:
                    self._image = image_settings
                    for image in self.batch_images:
                        self._image.add_item(image)


    def set_batch_image_with_containers(self, *args):
        self.select_rendernode_type = PoolImageMode.BATCH_IMAGE_WITH_CONTAINERS.value
        maya.delete_ui(self.image_config)
        self.image_config = []

        current_renderer = str(utils.get_current_scene_renderer())
        self.batchManagedImageWithContainersUI = BatchManagedImageWithContainersUI(self.poolImageFilter, self.rendernode_config, self.image_config, current_renderer)

    def set_custom_image(self, *args):
        self.select_rendernode_type = PoolImageMode.CUSTOM_IMAGE.value
        maya.delete_ui(self.image_config)
        self.image_config = []
        with utils.FrameLayout(
                    label="Custom Image Settings", collapsable=True,
                    width=325, collapse=False, parent = self.rendernode_config) as framelayout:
            self.image_config.append(framelayout)
          
            with utils.Row(2, 2, (140, 180), ("right","center"),
                            [(1, "top", 20),(2, "top", 15)],
                            parent = self.image_config[0]) as image_resource_id_row:
                self.image_config.append(image_resource_id_row)
                
                self.image_config.append(maya.text(label="Image Resource ID:   ", align="left",
                    annotation="Image Resource ID is visible in the portal under Images -> Select Image -> Resource ID.",
                    parent = self.image_config[0]))
                self.image_resource_id_field = maya.text_field(height=25, enable=True,
                    changeCommand=self.set_custom_image_resource_id,
                    annotation="Image Resource ID is visible in the portal under Images -> Select Image -> Resource ID.",
                    text = self.get_custom_image_resource_id(),
                    parent = self.image_config[0])

            with utils.Row(2, 2, (140, 180), ("right","center"),
                               [(1, "bottom", 20),(2,"bottom",15)],
                            parent = self.image_config[0]) as node_sku_id_row:
                self.image_config.append(node_sku_id_row)
                maya.text(label="Node Agent SKU ID:    ", align="left")
                with utils.Dropdown(
                    self.set_node_sku_id, 
                    parent = node_sku_id_row) as node_sku_id_dropdown:

                    self.image_config.append(node_sku_id_dropdown)
                    self._node_sku_id_dropdown = node_sku_id_dropdown 
                        
                    for nodeagentsku in self.base.node_agent_skus():
                        self._node_sku_id_dropdown.add_item(nodeagentsku)
                    
                    #check if we had to write the value to a temporary field because we read it during configure() before the dropdown was created
                    if self.node_sku_id:
                        self.select_node_sku_id(self.node_sku_id)

    def set_custom_image_with_containers(self, *args):
        self.select_rendernode_type = PoolImageMode.CUSTOM_IMAGE_WITH_CONTAINERS.value
        maya.delete_ui(self.image_config)
        self.image_config = []
        with utils.FrameLayout(
                    label="Custom Image with Container Settings", collapsable=True,
                    width=325, collapse=False, parent = self.rendernode_config) as framelayout:
            self.image_config.append(framelayout)
            with utils.Row(2, 2, (140, 180), ("right","center"),
                            [(1, "top", 20),(2, "top", 15)],
                            parent = self.image_config[0]) as image_resource_id_row:
                self.image_config.append(image_resource_id_row)
                self.image_config.append(maya.text(label="Image Resource ID:   ", align="left", 
                    annotation="Image Resource ID is visible in the portal under Images -> Select Image -> Resource ID.",
                    parent = self.image_config[0]))
                self.image_resource_id_field = maya.text_field(height=25, enable=True,
                    changeCommand=self.set_custom_image_resource_id,
                    annotation="Image Resource ID is visible in the portal under Images -> Select Image -> Resource ID.",
                    parent = self.image_config[0])

            with utils.Row(2, 2, (140, 180), ("right","center"),
                               [(1, "bottom", 20),(2,"bottom",15)],
                            parent = self.image_config[0]) as node_sku_id_row:
                self.image_config.append(node_sku_id_row)
                maya.text(label="Node Agent SKU ID:    ", align="left")
                with utils.Dropdown(
                    self.set_node_sku_id, 
                    parent = node_sku_id_row) as node_sku_id_dropdown:

                    self.image_config.append(node_sku_id_dropdown)
                    self._node_sku_id_dropdown = node_sku_id_dropdown 
                        
                    for nodeagentsku in self.base.node_agent_skus():
                        self._node_sku_id_dropdown.add_item(nodeagentsku)
                    
                    #check if we had to write the value to a temporary field because we read it during configure() before the dropdown was created
                    if self.node_sku_id:
                        self.select_node_sku_id(self.node_sku_id)

            registryTable = containerRegistryTable(self.image_config[0])

            imageTable = containerImageTable(self.image_config[0])