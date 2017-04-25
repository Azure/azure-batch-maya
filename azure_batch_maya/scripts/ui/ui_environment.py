#-------------------------------------------------------------------------
#
# Azure Batch Maya Plugin
#
# Copyright (c) Microsoft Corporation.  All rights reserved.
#
# MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the ""Software""), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED *AS IS*, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
#--------------------------------------------------------------------------

from api import MayaAPI as maya

import os
import utils

def edit_cell(*args):
    return 1

class EnvironmentUI(object):
    """
    Class to create the 'Env' tab in the plug-in UI
    """

    def __init__(self, base, frame, versions):
        """
        Create 'Env' tab and add to UI frame.

        :Args:
            - base (:class:`.AzureBatchEnvironemtn`): The base class for handling 
              Maya and plugin-related functionality.
            - frame (:class:`.AzureBatchUI`): The shared plug-in UI frame.
        """

        self.base = base
        self.label = " Env  "
        self.ready = False

        self.page = maya.form_layout(enableBackground=True)

        with utils.ScrollLayout(
            v_scrollbar=3, h_scrollbar=0, height=520) as scroll:

            with utils.RowLayout(row_spacing=20) as sublayout:

                with utils.FrameLayout(
                    label="Maya Version", collapsable=True, width=325):

                    with utils.ColumnLayout(
                        2, col_width=((1,160),(2,160)), row_spacing=(1,5),
                        row_offset=((1, "top", 15),(3, "bottom", 15))):

                        maya.text(
                            label="Use Maya version: ", align='right')

                        with utils.Dropdown(self.set_version) as v_settings:
                            self._maya_version = v_settings
                            for v in versions:
                                self._maya_version.add_item(v)

                        maya.text(
                            label="Use my license server: ", align='right')

                        self.use_license = maya.check_box(
                            label="", value=False, 
                            changeCommand=self.user_license_server)

                        self.custom_license_endp = maya.text_field(
                            placeholderText='License Server', enable=False)

                        self.custom_license_port = maya.text_field(
                            placeholderText='Port', enable=False )

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

                        with utils.ClickMenu(
                            self.insert_path, parent=self.custom_env_val,
                            button=3) as menu:

                            menu.add_item('<storage>')
                            menu.add_item('<maya_root>')
                            menu.add_item('<user_scripts>')
                            menu.add_item('<user_modules>')
                            menu.add_item('<temp_dir>')

                        maya.button(
                            label="Add", command=self.add_row)

                        maya.button(
                            label="Delete", command=self.delete_row)

                with utils.FrameLayout(
                    label="Plugins", collapsable=True,
                    width=325, collapse=True):

                    with utils.ColumnLayout(
                        2, col_width=((1,180),(2,140))) as plugin_layout:

                        self.plugin_layout = plugin_layout

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
        """
        Remove selected row from user environment variables table.
        """
        selected_row = maya.table(self.env_vars, query=True, selectedRow=True)
        maya.table(self.env_vars, edit=True, deleteRow=selected_row)

    def add_row(self, *args):
        """
        Add new user environment variable from contents of custom_env text
        fields.
        """
        env_var = maya.text_field(self.custom_env_var, query=True, text=True)
        env_val = maya.text_field(self.custom_env_val, query=True, text=True)
        if env_var and env_val:
            maya.table(self.env_vars, edit=True, insertRow=1)

    def populate_row(self, row, column):
        """
        Add data to table cell. Command called by table getCell automatically
        when new row is added.

        :Args:
            - row (int): Selected row index.
            - column (int): Selected column index.
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

    def set_version(self, version):
        """
        Set Maya version to run on server. Command for version dropdown
        selection.

        :Args:
            - version (str): The selected version string, e.g. ``Maya Beta``.
        """
        self.base.set_version(version)

    def insert_path(self, path):
        """
        Insert a path place holder into an environment variable value.
        Command for text field right-click menu selection.

        :Args:
            - path (string): One of the place holder values from the menu,
              e.g. ``<storage>, <maya_root>``.
        """
        maya.text_field(self.custom_env_val, edit=True, insertText=path)

    def get_env_vars(self):
        """
        Retrieve all user environment variables.

        :Returns:
            - Environment variables as a dictionary.
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

    def user_license_server(self, enabled):
        """
        Enable use of custom Maya license server. Command for use_license
        check box.

        :Args:
            - enabled (bool): Whether to use custom license server.
        """
        maya.text_field(self.custom_license_endp, edit=True, enable=enabled)
        maya.text_field(self.custom_license_port, edit=True, enable=enabled)

    def get_license_server(self):
        license = {"LicenseServer":"", "LicensePort":""}
        enabled = maya.check_box(self.use_license, query=True, value=True)

        if enabled:
            license["LicenseServer"] = str(maya.text_field(
                self.custom_license_endp, query=True, text=True))

            license["LicensePort"] = str(maya.text_field(
                self.custom_license_port, query=True, text=True))

        return license

    def refresh(self, *args):
        """
        Clear any data and customization. Command for refresh_button.
        """
        maya.table(self.env_vars, edit=True, clearTable=True, rows=0)
        self.base.refresh()
        maya.refresh()

    def is_logged_in(self):
        """
        Called when the plug-in is authenticated. Enables UI.
        """
        maya.form_layout(self.page, edit=True, enable=True)

    def is_logged_out(self):
        """
        Called when the plug-in is logged out. Disables UI and resets
        whether that tab has been loaded for the first time.
        """
        maya.form_layout(self.page, edit=True, enable=False)
        self.ready = False

    def prepare(self):
        """
        Called when the tab is loaded (clicked into) for the first time.
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