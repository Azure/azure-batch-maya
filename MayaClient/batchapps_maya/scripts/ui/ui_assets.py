#-------------------------------------------------------------------------
#
# Batch Apps Maya Plugin
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

class AssetsUI:

    def __init__(self, base, frame):

        self.base = base
        self.label = " Assets "
        self.ready = False
        
        with utils.RowLayout(width=360) as layout:
            self.page = layout

            with utils.ScrollLayout(v_scrollbar=3, h_scrollbar=0, height=475, width=355):
                with utils.RowLayout(row_spacing=20, width=330) as sublayout:
                    self.asset_display = sublayout

            with utils.ColumnLayout(1, col_width=(1,355)):
                with utils.ColumnLayout(2, col_width=((1, 177),(2, 177))):
                       maya.button(label="Add Files", command=self.add_asset)
                       maya.button(label="Add Directory", command=self.add_dir)

                self.upload_button = maya.button(label="Upload", command=self.upload)
                maya.button(label="Refresh", command=self.refresh)

        frame.add_tab(self)
        self.is_logged_out()

    def refresh(self, *args):
        self.clear_ui()
        maya.refresh()
        self.base.set_assets()

        for cat in self.base.asset_categories():
            self.list_display(cat)

        self.user_assets = self.list_display('Additional')

    def upload(self, *args):
        self.base.upload()

    def upload_status(self, status):
        maya.button(self.upload_button, edit=True, label=status)
        maya.refresh()

    def disable(self, enabled):
        maya.row_layout(self.page, edit=True, enable=enabled)

    def list_display(self, label):
        with utils.FrameLayout(label=label, collapsable=True, width=325,
                         parent=self.asset_display):

            with utils.ScrollLayout(v_scrollbar=3, h_scrollbar=0) as scroll:
                with utils.ColumnLayout(2) as layout:

                    for f in self.base.get_assets(label):
                        f.display(layout, scroll)

                    return (layout, scroll)

    def clear_ui(self):
        children = maya.row_layout(self.asset_display,
                                   query=True,
                                   childArray=True)
        if not children:
            return

        for child in children:
            maya.delete_ui(child, control=True)

    def add_asset(self, *args):
        cap = "Select additional rendering assets"
        fil = "All Files (*.*)"
        okCap = "Add Files"
        new_files = maya.file_select(fileFilter=fil,
                                     fileMode=4,
                                     okCaption=okCap,
                                     caption=cap)
        if not new_files:
            return

        self.base.add_files(new_files, self.user_assets)
        

    def add_dir(self, *args):
        cap = "Select directory of assets"
        okCap = "Add Folder"
        new_dir = maya.file_select(fileMode=3, okCaption=okCap, caption=cap)
        if not new_dir:
            return

        self.base.add_dir(new_dir, self.user_assets)

    def is_logged_in(self):
        maya.col_layout(self.page, edit=True, enable=True)

    def is_logged_out(self):
        maya.col_layout(self.page, edit=True, enable=False)
        self.ready = False

    def prepare(self):
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
