# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import utils

from api import MayaAPI as maya


def edit_cell(*args):
    return 1


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
        with utils.ScrollLayout(
            v_scrollbar=3, h_scrollbar=0, height=520) as scroll:

            with utils.RowLayout(row_spacing=20) as sublayout:
                with utils.FrameLayout(
                    label="Render Node Configuration", collapsable=True, width=325):

                    with utils.ColumnLayout(
                        2, col_width=((1,160),(2,160)), row_spacing=(1,5),
                        row_offset=((1, "top", 15),(5, "bottom", 15))):
                        maya.text(label="Use Image: ", align='right')
                        with utils.Dropdown(self.set_image) as image_settings:
                            self._image = image_settings
                            for image in images:
                                self._image.add_item(image)
                        maya.text(label="Use VM Type: ", align='right')
                        with utils.Dropdown(self.set_sku) as sku_settings:
                            self._sku = sku_settings
                            for sku in skus:
                                self._sku.add_item(sku)
                        maya.text(label="Use licenses: ", align='right')
                        for label, checked in licenses.items():
                            self.license_settings[label] = maya.check_box(
                                    label=label, value=checked, changeCommand=self.use_license_server)
                            maya.text(label="", align='right')

                with utils.FrameLayout(
                    label="Environment Variables", collapsable=True,
                    width=325, collapse=True):
                    with utils.Row(1,1,325):
                        self.env_vars = maya.table(
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

    def set_image(self, image):
        """Set VM image to run on the render node. Command for image dropdown
        selection. This value will be stored in the config file.
        :param str image: The selected image name, e.g. 'Batch Windows Preview'.
        """
        self.base.set_image(image)

    def get_image(self):
        """Retrieve the currently selected image name."""
        return self._image.value()

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
        self.base.set_sku(sku)

    def get_sku(self):
        """Retrieve the currently selected VM SKU."""
        return self._sku.value()

    def select_sku(self, sku):
        """Selected the cached SKU value if available."""
        # TODO: Validate against SKU list.
        if sku:
            self._sku.select(sku)

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
            vars[str(row_key[0])] = str(row_val[0])
        return vars

    def use_license_server(self, enabled):
        """Enable the license service for the specified apps.
        Enable use of custom Maya license server. Command for use_license
        check box.
        """
        for label, checkbox in self.license_settings.items():
            checked = maya.check_box(checkbox, query=True, value=True)
            self.base.licenses[label] = checked

    def refresh_licenses(self):
        """Refresh the use of plugin licenses based on scene."""
        for label, checked in self.base.licenses.items():
            maya.check_box(self.license_settings[label], edit=True, value=checked)

    def refresh(self, *args):
        """Clear any data and customization. Command for refresh_button."""
        maya.table(self.env_vars, edit=True, clearTable=True, rows=0)
        self.base.refresh()
        self.refresh_licenses()
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