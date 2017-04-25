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

import os
import utils

from api import MayaAPI as maya


class AssetsUI(object):
    """Class to create the 'Assets' tab in the plug-in UI"""

    def __init__(self, base, frame):
        """Create 'Assets' tab and add to UI frame.

        :param base: The base class for handling asset-related functionality.
        :type base: :class:`.AzureBatchAssets`
        :param frame: The shared plug-in UI frame.
        :type frame: :class:`.AzureBatchUI`
        """
        self.base = base
        self.label = "Assets"
        self.ready = False
        self.page = maya.form_layout(enableBackground=True)
        with utils.Row(2, 2, (70,260), ("left","left")) as proj:
                maya.text(label="Project:    ", align="left")
                self._asset_group = maya.text_field(height=25, enable=True)

        with utils.ScrollLayout(
            v_scrollbar=3, h_scrollbar=0, height=450) as scroll:
            self.scroll_layout = scroll
            with utils.ColumnLayout(2) as sublayout:
                self.asset_display = sublayout
        f_btn = maya.button(label="Add Files", command=self.add_asset)
        d_btn = maya.button(label="Add Directory", command=self.add_dir)

        with utils.Row(1, 1, 355) as u_btn:
            self.upload_button = utils.ProcButton(
                "Upload",  "Uploading...", self.upload)

        with utils.Row(1, 1, 355, "center", (1,"bottom",0)) as r_btn:
            self.refresh_button = utils.ProcButton(
                "Refresh", "Refreshing...", self.refresh)

        maya.form_layout(
            self.page, edit=True,
            attachForm=[(proj, 'left', 5), (proj, 'right', 5),
                        (proj,'top', 5),
                        (scroll, 'left', 5), (scroll, 'right', 5),
                        (f_btn, 'left', 5),(d_btn,'right',5),
                        (u_btn, 'left', 0),(u_btn,'right',0),
                        (r_btn, 'bottom', 5),
                        (r_btn, 'left', 0),(r_btn,'right',0)],
            attachControl=[(proj, "bottom", 5, scroll),
                           (proj, "bottom", 5, scroll),
                           (scroll, "bottom", 5, f_btn),
                           (scroll, "bottom", 5, d_btn),
                           (f_btn, "bottom" , 5, u_btn),
                           (d_btn, "bottom", 5, u_btn),
                           (u_btn, "bottom",5,r_btn)],
            attachPosition=[(f_btn, 'right', 5, 50),
                            (d_btn, 'left', 5, 50)])
        frame.add_tab(self)
        self.is_logged_out()

    def refresh(self, *args):
        """Refresh Assets tab. Command for refresh_button.
        Remove all existing UI elements and gathered
        assets and re-build from scratch. This is also called to populate 
        the tab for the first time.
        """
        self.refresh_button.start()
        self.clear_ui()
        maya.refresh()
        project_name = self.base.get_project()
        maya.text_field(self._asset_group, edit=True, text=project_name)
        self.base.set_assets()
        for f in self.base.get_assets():
            f.display(self, self.asset_display, self.scroll_layout)
        self.refresh_button.finish()

    def upload(self, *args):
        """Upload gathered assets. Command for upload_button.
        Calls the base upload function.
        """
        self.base.upload()

    def upload_status(self, status):
        """Report upload status in UI. Called from base class.
        Displays status in the upload_button label.
        :param str status: The status string to display.
        """
        self.upload_button.update(status)

    def disable(self, enabled):
        """Disable the tab from user interaction. Used during long running
        processes like upload, and when plug-in is unauthenticated.
        :param bool enabled: Whether to enable the display. False will
         disable the display.
        """
        maya.form_layout(self.page, edit=True, enable=enabled)

    def clear_ui(self):
        """Wipe all UI elements in the Assets tab."""
        children = maya.col_layout(self.asset_display,
                                   query=True,
                                   childArray=True)
        if not children:
            return
        for child in children:
            maya.delete_ui(child, control=True)

    def add_asset(self, *args):
        """Add one or more individual asset files to the collection.
        Command for the 'Add Files' button. 
        """
        cap = "Select additional rendering assets"
        fil = "All Files (*.*)"
        okCap = "Add Files"
        new_files = maya.file_select(fileFilter=fil,
                                     fileMode=4,
                                     okCaption=okCap,
                                     caption=cap)
        if not new_files:
            return
        self.base.add_files(new_files, self.asset_display, self.scroll_layout)
        

    def add_dir(self, *args):
        """Add all the files from a specified directory as assets to the 
        collection. Command for the 'Add Directory' button.
        """
        cap = "Select directory of assets"
        okCap = "Add Folder"
        new_dir = maya.file_select(fileMode=3, okCaption=okCap, caption=cap)
        if not new_dir:
            return
        self.base.add_dir(new_dir, self.asset_display, self.scroll_layout)

    def is_logged_in(self):
        """Called when the plug-in is authenticated. Enables UI."""
        maya.form_layout(self.page, edit=True, enable=True)

    def is_logged_out(self):
        """Called when the plug-in is logged out. Disables UI and resets
        whether that tab has been loaded for the first time.
        """
        maya.form_layout(self.page, edit=True, enable=False)
        self.ready = False

    def get_project(self):
        return maya.text_field(self._asset_group, query=True, text=True)

    def prepare(self):
        """Called when the tab is loaded (clicked into) for the first time.
        Initiates the gathering of assets and preparing of UI elements.
        Once loaded, remains so for the rest of the plug-in session unless
        logged out or manually refreshed.
        If loading the UI fails, the tab returns to a logged-out state.
        """
        if not self.ready:
            maya.refresh()
            try:
                self.refresh()
                self.is_logged_in()
                self.ready = True
            except Exception as exp:
                maya.error("Error starting Assets UI: {0}".format(exp))
                self.is_logged_out()
        maya.refresh()
