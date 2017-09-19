# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import azurebatchutils as utils

from azurebatchmayaapi import MayaAPI as maya


class ConfigUI(object):
    """Class to create the 'Config' tab in the plug-in UI"""

    def __init__(self, base, frame):
        """Create 'Config' tab and add to UI frame.

        :param base: The base class for handling configuration and
         auth-related functionality.
        :type base: :class:`.AzureBatchConfig`
        :param frame: The shared plug-in UI frame.
        :type frame: :class:`.AzureBatchUI`
        """
        self.base = base
        self.label = "Config"
        self.ready = False
        self.page = maya.form_layout()

        with utils.ScrollLayout(height=520, parent=self.page) as scroll:
            self.heading = maya.text(label="Authenticating plug-in...",
                                        align="center", font="boldLabelFont")
            with utils.Row(2, 2, (70,260), ("left","left"),
                           [(1, "top", 15),(2,"top",15)]):
                maya.text(label="Status: ", align="left")
                self.auth_status = maya.text(label="", align="left")
            
            with utils.Row(2, 2, (70,260), ("left","left")):
                maya.text(label="Service:    ", align="left")
                self._endpoint = maya.text_field(height=25, enable=True)
            
            #TODO: Allow set to 0 to disable threads
            with utils.Row(2, 2, (70,260), ("left","left")):
                maya.text(label="Threads:    ", align="left")
                self._threads = maya.int_field(
                    changeCommand=self.set_threads,
                    height=25,
                    minValue=1,
                    maxValue=40,
                    enable=True,
                    value=20)
            
            with utils.Row(2, 2, (70,260), ("left","center"),
                           [(1, "bottom", 20),(2,"bottom",15)]):
                maya.text(label="Logging:    ", align="left")
                with utils.Dropdown(self.set_logging) as log_settings:
                    self._logging = log_settings
                    self._logging.add_item("Debug")
                    self._logging.add_item("Info")
                    self._logging.add_item("Warning")
                    self._logging.add_item("Error")

            box_label = "Azure Authentication Settings"
            with utils.FrameLayout(label=box_label, collapsable=True):
                with utils.Row(2, 2, (140, 180), ("right","center"),
                               [(1, "top", 20),(2, "top", 15)]):
                    maya.text(label="Batch Account:   ", align="right")
                    self._account = maya.text_field(height=25, enable=True)

                with utils.Row(2, 2, (140, 180), ("right","center"),
                               [(1, "bottom", 20),(2,"bottom",15)]):
                    maya.text(label="Batch Key:   ", align="right")
                    self._key = maya.text_field(height=25, enable=True)

                with utils.Row(2, 2, (140, 180), ("right","center"),
                               [(1, "bottom", 20),(2,"bottom",15)]):
                    maya.text(label="Storage Account:   ", align="right")
                    self._storage = maya.text_field(height=25, enable=True)

                with utils.Row(2, 2, (140, 180), ("right","center"),
                               [(1, "bottom", 20),(2,"bottom",15)]):
                    maya.text(label="Storage Key:   ", align="right")
                    self._storage_key = maya.text_field(height=25, enable=True)

        with utils.Row(1, 1, 355, "center", (1, "bottom",0)) as btn:
            self._authenticate = maya.button(label="Authenticate",
                                             command=self.authenticate,
                                             enable=True)
        maya.form_layout(self.page, edit=True,
                         attachForm=[(scroll, 'top', 5),
                                     (scroll, 'left', 5), (scroll, 'right', 5),
                                     (btn, 'bottom', 5),
                                     (btn, 'left', 0), (btn, 'right', 0)],
                         attachControl=(scroll, "bottom", 5, btn))
        frame.add_tab(self)
        maya.form_layout(self.page, edit=True, enable=False)
        maya.refresh()

    @property
    def endpoint(self):
        """AzureBatch Service Endpoint. Retrieves contents of text field."""
        return maya.text_field(self._endpoint, query=True, text=True)

    @endpoint.setter
    def endpoint(self, value):
        """AzureBatch Service Endpoint. Sets contents of text field."""
        maya.text_field(self._endpoint, edit=True, text=str(value))

    @property
    def threads(self):
        """Max number of threads used. Retrieves contents of int field."""
        return maya.int_field(self._threads, query=True, value=True)

    @threads.setter
    def threads(self, value):
        """Max number of threads used. Sets contents of iny field."""
        maya.int_field(self._threads, edit=True, value=int(value))

    @property
    def account(self):
        """AzureBatch Unattended Account ID. Retrieves contents of text field."""
        return maya.text_field(self._account, query=True, text=True)

    @account.setter
    def account(self, value):
        """AzureBatch Unattended Account ID. Sets contents of text field."""
        maya.text_field(self._account, edit=True, text=str(value))

    @property
    def key(self):
        """AzureBatch Unattended Account Key. Retrieves contents of text field."""
        return maya.text_field(self._key, query=True, text=True)

    @key.setter
    def key(self, value):
        """AzureBatch Unattended Account Key. Sets contents of text field."""
        maya.text_field(self._key, edit=True, text=str(value))

    @property
    def storage(self):
        """AzureBatch AAD Client ID. Retrieves contents of text field."""
        return maya.text_field(self._storage, query=True, text=True)

    @storage.setter
    def storage(self, value):
        """AzureBatch AAD Client ID. Sets contents of text field."""
        maya.text_field(self._storage, edit=True, text=str(value))

    @property
    def storage_key(self):
        """AzureBatch AAD Tenant. Retrieves contents of text field."""
        return maya.text_field(self._storage_key, query=True, text=True)

    @storage_key.setter
    def storage_key(self, value):
        """AzureBatch AAD Tenant. Sets contents of text field."""
        maya.text_field(self._storage_key, edit=True, text=str(value))

    @property
    def status(self):
        """Plug-in authentication status. Sets contents of label."""
        return maya.text(self.auth_status, query=True, label=True)[8:]

    @status.setter
    def status(self, value):
        """Plug-in authentication status. Sets contents of label."""
        if value:
            maya.text(self.auth_status, edit=True, label="Authenticated", backgroundColor=[0.23, 0.44, 0.21])
        else:
            maya.text(self.auth_status, edit=True, label="Not authenticated", backgroundColor=[0.6, 0.23, 0.23])

    @property
    def logging(self):
        """Plug-in logging level. Retrieves selected level from dropdown."""
        return self._logging.selected() * 10

    @logging.setter
    def logging(self, value):
        """Plug-in logging level. Sets selected level from dropdown."""
        self._logging.select(int(value)/10)

    def is_logged_in(self):
        """Called when the plug-in is authenticated. Sets heading text."""
        maya.text(
            self.heading, edit=True, label="Authentication Configuration")
        maya.form_layout(self.page, edit=True, enable=True)

    def is_logged_out(self):
        """Called when the plug-in is logged out. Sets heading text."""
        maya.text(
            self.heading, edit=True, label="Authentication Configuration")
        maya.form_layout(self.page, edit=True, enable=True)

    def prepare(self):
        """Prepare Config tab contents - nothing needs to be done here as all
        loaded on plug-in start up.
        """
        pass

    def set_logging(self, level):
        """Set logging level. Command for logging dropdown selection.
        :param str level: The selected logging level, e.g. ``debug``.
        """
        self.base.set_logging(self.logging)

    def set_threads(self, threads):
        """Set number of threads. OnChange command for threads field.
        :param int threads: The selected number of threads.
        """
        self.base.set_threads(int(threads))

    def set_authenticate(self, auth):
        """Set label of authentication button depending on auth status.
        :param bool auth: Whether plug-in is authenticated.
        """
        self.status = auth
        if auth:
            maya.button(
                self._authenticate, edit=True, label="Refresh Authentication")
        else:
            maya.button(self._authenticate, edit=True, label="Authenticate")

    def authenticate(self, *args):
        """Initiate plug-in authentication, and save updated credentials
        to the config file.
        """
        self.base.save_changes()
        self.base.authenticate()
            