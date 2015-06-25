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

from maya import cmds

def edit_cell(*args):
    return 1

class EnvironmentUI:

    def __init__(self, base, frame, versions):

        self.base = base
        self.label = "  Env   "
        self.ready = False

        with utils.RowLayout(width=360) as layout:
            self.page = layout

            with utils.ScrollLayout(v_scrollbar=3, h_scrollbar=0, height=495, width=355):
                with utils.RowLayout(row_spacing=20) as sublayout:
                    with utils.FrameLayout(label="Maya Version", collapsable=True, width=325):
                        with utils.ColumnLayout(2, col_width=((1,160),(2,160)), row_spacing=(1,5),
                                    row_offset=((1, "top", 15),(3, "bottom", 15))):

                            cmds.text(label="Use Maya version: ", align='right')
                            with utils.Dropdown(self.set_version) as version_settings:
                                self._maya_version = version_settings
                                for v in versions:
                                    self._maya_version.add_item(v)

                            cmds.text(label="Use my license server: ", align='right')
                            self.use_license = maya.check_box(label="", value=False, changeCommand=self.user_license_server)
                            self.custom_license_endp = cmds.textFieldGrp( placeholderText='License Server', enable=False)
                            self.custom_license_port = cmds.textFieldGrp( placeholderText='Port', enable=False )

                    with utils.FrameLayout(label="Environment Variables", collapsable=True, width=325, collapse=True):
                        self.env_vars = cmds.scriptTable(rows=0, columns=2, label=[(1,"Setting"), (2,"Value")], columnWidth=[(1,155), (2,155)],
                                                    rowHeight=15, editable=False, selectionBehavior=1, getCellCmd=self.populate_row)

                        with utils.ColumnLayout(2, col_width=((1,160),(2,160))):
                            self.custom_env_var = cmds.textFieldGrp( placeholderText='Env Variable' )
                            self.custom_env_val = cmds.textFieldGrp( placeholderText='Value' )
                            popup = cmds.popupMenu(parent=self.custom_env_val, button=3) 
                            cmds.menuItem(label='<storage>', command=lambda a: self.insert_path("<storage>")) 
                            cmds.menuItem(label='<maya_root>', command=lambda a: self.insert_path("<maya_root>")) 
                            cmds.menuItem(label='<mentalray_root>', command=lambda a: self.insert_path("<mentalray_root>"))
                            cmds.menuItem(label='<arnold_root>', command=lambda a: self.insert_path("<arnold_root>"))
                            cmds.menuItem(label='<user_scripts>', command=lambda a: self.insert_path("<user_scripts>"))
                            cmds.menuItem(label='<user_modules>', command=lambda a: self.insert_path("<user_modules>"))
                            cmds.menuItem(label='<temp_dir>', command=lambda a: self.insert_path("<temp_dir>"))

                            addButton = cmds.button(label="Add",command=self.add_row)
                            deleteButton = cmds.button(label="Delete",command=self.delete_row)

                    with utils.FrameLayout(label="Plugins", collapsable=True, width=325, collapse=True):
                        with utils.ColumnLayout(2, col_width=((1,180),(2,140))) as plugin_layout:
                            self.plugin_layout = plugin_layout

            with utils.ColumnLayout(1, col_width=(1,355)):
                maya.button(label="Refresh", command=self.refresh)

        frame.add_tab(self)
        self.is_logged_out()

    def delete_row(self, *args):
        selected_row = cmds.scriptTable(self.env_vars, query=True, selectedRow=True)
        cmds.scriptTable(self.env_vars, edit=True, deleteRow=selected_row)

    def add_row(self, *args):
        env_var = cmds.textFieldGrp(self.custom_env_var, query=True, text=True )
        env_val = cmds.textFieldGrp(self.custom_env_val, query=True, text=True )
        if env_var and env_val:
            cmds.scriptTable(self.env_vars, edit=True, insertRow=1)

    def populate_row(self, row, column):
        if column == 1:
            env_var = cmds.textFieldGrp(self.custom_env_var, query=True, text=True )
            cmds.textFieldGrp(self.custom_env_var, edit=True, text="" )
            return env_var

        if column == 2:
            env_val = cmds.textFieldGrp(self.custom_env_val, query=True, text=True )
            cmds.textFieldGrp(self.custom_env_val, edit=True, text="" )
            return env_val

    def set_version(self, version):
        self.base.set_version(version)

    def insert_path(self, path):
        cmds.textFieldGrp(self.custom_env_val, edit=True, insertText=path)

    def get_env_vars(self):
        vars = {}
        rows = cmds.scriptTable(self.env_vars, query=True, rows=True)
        for row in range(1, rows):
            row_key = cmds.scriptTable(self.env_vars, cellIndex=(row, 1), query=True, cellValue=True)
            row_val = cmds.scriptTable(self.env_vars, cellIndex=(row, 2), query=True, cellValue=True)
            vars[str(row_key[0])] = str(row_val[0])

        return vars

    def user_license_server(self, enabled):
        cmds.textFieldGrp(self.custom_license_endp, edit=True, enable=enabled)
        cmds.textFieldGrp(self.custom_license_port, edit=True, enable=enabled)

    def refresh(self, *args):
        cmds.scriptTable(self.env_vars, edit=True, clearTable=True, rows=0)
        self.base.refresh()
        maya.refresh()

    def is_logged_in(self):
        maya.col_layout(self.page, edit=True, enable=True)

    def is_logged_out(self):
        maya.col_layout(self.page, edit=True, enable=False)
        self.ready = False

    def prepare(self):
        if not self.ready:
            maya.refresh()
            try:
                self.is_logged_in()
                self.ready = True

            except Exception as exp:
                maya.error("Error starting Environment UI: {0}".format(exp))
                self.is_logged_out()

        maya.refresh()