# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import azurebatchutils as utils

from azurebatchmayaapi import MayaAPI as maya


class ConfigUI(object):
    """Class to create the 'Config' tab in the plug-in UI"""

    def __init__(self, base, settings, frame):
        """Create 'Config' tab and add to UI frame.

        :param base: The base class for handling configuration and
         auth-related functionality.
        :type base: :class:`.AzureBatchConfig`
        :param frame: The shared plug-in UI frame.
        :type frame: :class:`.AzureBatchUI`
        """
        self.base = base
        self.settings = settings
        self.label = "Config"
        self.ready = False
        self.page = maya.form_layout()
        self.frame = frame
        self.batchAccountRow = None
        self.account_ui_elements = None

        with utils.ScrollLayout(height=520, parent=self.page, width=325) as auth_layout:
            self.auth_layout = auth_layout
            self.heading = maya.text(label="Authenticating plug-in...", align="center", font="boldLabelFont", wordWrap=True)
            frame.add_tab(self)
            maya.form_layout(self.page, edit=True, enable=False)
            maya.refresh()
    
    def init_post_auth(self):
        maya.delete_ui(self.auth_layout)
        with utils.ScrollLayout(height=520, parent=self.page, width=325) as scroll:
            box_label = "Batch Account Settings"
            with utils.FrameLayout(label=box_label, collapsable=True) as account_settings_frame:
                self.account_settings_frame = account_settings_frame
                with utils.Row(2, 2, (90,210), ("left","left"),
                                [(1, "top", 15),(2,"top",15)]):
                    maya.text(label="Status: ", align="left")
                    self.auth_status = maya.text(label="", align="left")

                with utils.Row(2, 2, (90,210), ("left","left")) as subscriptionRow:
                    maya.text(label="Subscription:    ", align="left")

                    with utils.Dropdown(self.select_subscription_in_dropdown) as subscription_dropdown:
                        self._subscription_dropdown = subscription_dropdown
                        subscriptions = self.base.available_subscriptions()
                        self.subscriptions_by_displayname = dict([ (sub.display_name, sub) for sub in subscriptions ])
                        for sub in subscriptions:
                            self._subscription_dropdown.add_item(sub.display_name)

        self.disable(True)
        maya.form_layout(self.page, edit=True, enable=True)
        maya.refresh()

    def init_after_subscription_selected(self, selected_subscription):
        maya.delete_ui(self.batchAccountRow)
        with utils.Row(2, 2, (90,210), ("left","left"), parent=self.account_settings_frame) as batchAccountRow:
            self.batchAccountRow = batchAccountRow
            maya.text(label="Batch Account:    ", align="left")
            maya.refresh()
            with utils.Dropdown(self.select_account_in_dropdown) as account_dropdown:
                self._account_dropdown = account_dropdown
                accounts = self.base.available_batch_accounts()
                self.accounts_by_name = dict([ (account.name, account) for account in accounts ])
                for account in accounts:
                    self._account_dropdown.add_item(account.name)

    def init_after_batch_account_selected(self):
        maya.delete_ui(self.account_ui_elements)
        self.account_ui_elements = []
        with utils.Row(2, 2, (90, 210), ("left","left"),[(1, "bottom", 20),(2,"bottom",15)], parent=self.account_settings_frame) as storageAccountRow:
            self.account_ui_elements.append(storageAccountRow)
            maya.text(label="Storage Account:   ", align="right")
            self.storage_account_field = maya.text_field(height=25, enable=True, editable=False, text=self.base.storage_account)

        #TODO: Allow set to 0 to disable threads
        with utils.Row(2, 2, (90,210), ("left","left"), parent=self.account_settings_frame) as threadsRow:
            self.account_ui_elements.append(storageAccountRow)
            maya.text(label="Threads:    ", align="left")
            self._threads = maya.int_field(
                changeCommand=self.set_threads,
                height=25,
                minValue=1,
                maxValue=40,
                enable=True,
                value=20)
            
        with utils.Row(2, 2, (90,210), ("left","center"),
                        [(1, "bottom", 20),(2,"bottom",15)], parent=self.account_settings_frame) as loggingRow:
            self.account_ui_elements.append(loggingRow)
            maya.text(label="Logging:    ", align="left")
            with utils.Dropdown(self.set_logging) as log_settings:
                self._logging = log_settings
                self._logging.add_item("Debug")
                self._logging.add_item("Info")
                self._logging.add_item("Warning")
                self._logging.add_item("Error")
        
        self.settings.init_after_account_selected()

    def get_selected_subscription_from_dropdown(self):
        """Retrieve the currently selected image name."""
        return self._subscription_dropdown.value()

    def select_subscription_in_dropdown(self, sub_displayname):
        """Select the cached image value if available."""
        # TODO: Check value against current lists. 
        if sub_displayname:
            self._subscription_dropdown.select(sub_displayname)
            self.selected_subscription = self.subscriptions_by_displayname[sub_displayname]
            self.subscription = sub_displayname
            self.base.init_after_subscription_selected(self.selected_subscription.subscription_id, sub_displayname)
            self.init_after_subscription_selected(self.selected_subscription)

    def select_account_in_dropdown(self, account_displayName):
        if account_displayName:
            self._account_dropdown.select(account_displayName)
            self.selected_batchaccount = self.accounts_by_name[account_displayName]
            self.base.init_after_batch_account_selected(self.selected_batchaccount, self.selected_subscription.subscription_id)
            self.init_after_batch_account_selected()

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
        try:
            return self._logging.selected() * 10
        except AttributeError:
            return self.base.default_logging()

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

    def prompt_for_login(self, value):
        """Called when the plug-in is prompting for authentication login. Sets heading text."""
        maya.text(
            self.heading, edit=True, label=value)
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
    
    def disable(self, enabled):
        """Disable the tab from user interaction. Used during long running
        processes like upload, and when plug-in is unauthenticated.
        :param bool enabled: Whether to enable the display. False will
         disable the display.
        """
        maya.form_layout(self.page, edit=True, enable=enabled)