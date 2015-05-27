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

import utils


class ConfigUI(object):

    def __init__(self, base, frame):

        self.base = base
        self.label = " Config "
        self.ready = False

        with utils.RowLayout(width=360) as layout:
            self.page = layout

            with utils.ScrollLayout(height=520, parent=self.page) as col:
                self.heading = maya.text(label="Authenticating plug-in...",
                                         align="center", font="boldLabelFont")
            
                with utils.ColumnLayout(2, col_width=((1, 50),(2, 280)), row_spacing=(1,5),
                                    row_offset=((1, "top", 15),(2, "bottom", 15))) as cols:

                    maya.text(label="Status: ", align="left")
                    self.auth_status = maya.text(label="", align="left")
                    maya.text(label="Service:    ", align="left")
                    self._endpoint = maya.text_field(width=280,
                                                    height=25,
                                                    enable=True,
                                                    changeCommand=self.changes_detected)
                    maya.text(label="Logging:    ", align="left")
                    with utils.Dropdown(self.set_logging) as log_settings:
                        self._logging = log_settings
                        self._logging.add_item("Debug")
                        self._logging.add_item("Info")
                        self._logging.add_item("Warning")
                        self._logging.add_item("Error")

                    maya.text(label="")

                box_label = "Attended Configuration Settings"
                with utils.FrameLayout(label=box_label, width=360, collapsable=True, parent=col) as box:

                    with utils.ColumnLayout(2, col_width=((1, 120),(2, 200)), row_spacing=(1,10),
                                      row_offset=((1, "top", 10),(3, "bottom", 15))) as cols:

                        maya.text(label="Client ID   ", align="right")
                        self._client = maya.text_field(width=200,
                                                        height=25,
                                                        enable=True,
                                                        changeCommand=self.changes_detected)

                        maya.text(label="Tenant   ", align="right")
                        self._tenant = maya.text_field(width=200,
                                                        height=25,
                                                        enable=True,
                                                        changeCommand=self.changes_detected)

                        maya.text(label="Redirect URI   ", align="right")
                        self._redirect = maya.text_field(width=200,
                                                        height=25,
                                                        enable=True,
                                                        changeCommand=self.changes_detected)


                box_label = "Unattended Configuration Settings"
                with utils.FrameLayout(label=box_label, width=360, collapsable=True, parent=col) as box:

                    with utils.ColumnLayout(2, col_width=((1, 120),(2, 200)), row_spacing=(1,10),
                                      row_offset=((1, "top", 10),(2, "bottom", 15))) as cols:

                        maya.text(label="Unattended Account   ", align="right")
                        self._account = maya.text_field(width=200,
                                                        height=25,
                                                        enable=True,
                                                        changeCommand=self.changes_detected)

                        maya.text(label="Unattended Key   ", align="right")
                        self._key = maya.text_field(width=200,
                                                    height=25,
                                                    enable=True,
                                                    changeCommand=self.changes_detected)


            with utils.ColumnLayout(2, col_width=((1, 180),(2, 180)), row_spacing=(1,10),
                              parent=self.page) as cols:

                self._save_cfg = maya.button(label="Save Changes",
                                             command=self.save_changes,
                                             width=180,
                                             enable=False)


                self._authenticate = maya.button(label="Authenticate",
                                                 command=self.authenticate,
                                                 width=180,
                                                 enable=True)

        frame.add_tab(self)
        maya.row_layout(self.page, edit=True, enable=False)
        maya.refresh()

    @property
    def endpoint(self):
        return maya.text_field(self._endpoint, query=True, text=True)

    @endpoint.setter
    def endpoint(self, value):
        maya.text_field(self._endpoint, edit=True, text=str(value))


    @property
    def account(self):
        return maya.text_field(self._account, query=True, text=True)

    @account.setter
    def account(self, value):
        maya.text_field(self._account, edit=True, text=str(value))


    @property
    def key(self):
        return maya.text_field(self._key, query=True, text=True)

    @key.setter
    def key(self, value):
        maya.text_field(self._key, edit=True, text=str(value))


    @property
    def client(self):
        return maya.text_field(self._client, query=True, text=True)

    @client.setter
    def client(self, value):
        maya.text_field(self._client, edit=True, text=str(value))


    @property
    def tenant(self):
        return maya.text_field(self._tenant, query=True, text=True)

    @tenant.setter
    def tenant(self, value):
        maya.text_field(self._tenant, edit=True, text=str(value))


    @property
    def redirect(self):
        return maya.text_field(self._redirect, query=True, text=True)

    @redirect.setter
    def redirect(self, value):
        maya.text_field(self._redirect, edit=True, text=str(value))


    @property
    def status(self):
        return maya.text(self.auth_status, query=True, label=True)[8:]

    @status.setter
    def status(self, value):
        maya.text(self.auth_status, edit=True, label=value)


    @property
    def logging(self):
        return self._logging.selected() * 10

    @logging.setter
    def logging(self, value):
        self._logging.select(int(value)/10)

    def is_logged_in(self):
        maya.text(self.heading, edit=True, label="Authentication Configuration")
        maya.row_layout(self.page, edit=True, enable=True)

    def is_logged_out(self):
        maya.text(self.heading, edit=True, label="Authentication Configuration")
        maya.row_layout(self.page, edit=True, enable=True)

    def prepare(self):
        pass

    def changes_detected(self, *args):
        maya.button(self._save_cfg, edit=True, enable=True)

    def save_changes(self, *args):
        self.base.save_changes()
        maya.button(self._save_cfg, edit=True, enable=False)

    def set_logging(self, level):
        self.changes_detected()
        self.base.set_logging(level.lower())

    def set_authenticate(self, auth):
        if auth:
            maya.button(self._authenticate, edit=True, label="Refresh Authentication")
        else:
            maya.button(self._authenticate, edit=True, label="Authenticate")

    def authenticate(self, *args):
        self.base.authenticate()
            