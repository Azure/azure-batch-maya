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
        self.subscription_row = None
        self.batch_account_row = None
        self.account_ui_elements = None
        self.subscription_ui_elements = None

        self.auth_layout_elements = []
        with utils.ScrollLayout(height=520, parent=self.page, width=375) as auth_layout:
            self.auth_layout = auth_layout
            self.auth_layout_elements.append(auth_layout)
            self.heading = maya.text(label="Authenticating plug-in...", align="center", font="boldLabelFont", wordWrap=True)
        maya.form_layout(self.page, edit=True, enable=False)
        frame.add_tab(self)
        maya.refresh()

    def change_subscription_button_pressed(self, *args):
        self.status = "Loading"
        maya.refresh()
        maya.form_layout(self.page, edit=True, enable=False)

        maya.menu(self._subscription_dropdown.menu, edit=True, deleteAllItems=True, enable=True)
        maya.delete_ui(self._change_subscription_button)
        if self.batch_account_row is not None:
            maya.delete_ui(self.batch_account_row)
        if self.account_ui_elements:
            maya.delete_ui(self.account_ui_elements)
        self.account_ui_elements = []
        subscriptions = self.base.available_subscriptions()
        self.subscriptions_by_displayname = dict([ (sub.display_name, sub) for sub in subscriptions ])
        self._subscription_dropdown.add_item("")    #dummy value so dropdown appears empty
        for sub in subscriptions:
            self._subscription_dropdown.add_item(sub.display_name)
        maya.menu(self._subscription_dropdown.menu, edit=True, enable=True, width=257)
        self.status = "Please select Subscription"

        #TODO: Allow set to 0 to disable threads
        with utils.Row(2, 2, (100,200), ("left","left"), parent=self.account_settings_frame) as threadsRow:
            self.account_ui_elements.append(threadsRow)
            maya.text(label="Threads:    ", align="left")
            self._threads = maya.int_field(
                changeCommand=self.set_threads,
                height=25,
                minValue=1,
                maxValue=40,
                enable=True,
                value=self.base.threads)
            
        with utils.Row(2, 2, (100,200), ("left","center"),
                        [(1, "bottom", 20),(2,"bottom",15)], parent=self.account_settings_frame) as loggingRow:
            self.account_ui_elements.append(loggingRow)
            maya.text(label="Logging:    ", align="left")
            with utils.Dropdown(self.set_logging) as log_settings:
                self._logging = log_settings
                self._logging.add_item("Debug")
                self._logging.add_item("Info")
                self._logging.add_item("Warning")
                self._logging.add_item("Error")
        maya.form_layout(self.page, edit=True, enable=True)
        maya.refresh()

    def change_batch_account_button_pressed(self, *args):
        self.status = "Loading"
        maya.refresh()
        maya.form_layout(self.page, edit=True, enable=False)
        maya.menu(self._account_dropdown.menu, edit=True, deleteAllItems=True)
        maya.delete_ui(self._change_batch_account_button)
        if self.account_ui_elements:
            maya.delete_ui(self.account_ui_elements)
        self.account_ui_elements = []
        maya.menu(self._account_dropdown.menu, edit=True, enable=True, width=257)
        accounts = self.base.available_batch_accounts()
        self.accounts_by_name = dict([ (account.name, account) for account in accounts ])
        self._account_dropdown.add_item("")     #dummy value so dropdown appears empty
        for account in accounts:
            self._account_dropdown.add_item(account.name)
        self.status = "Authenticated"

        #TODO: Allow set to 0 to disable threads
        with utils.Row(2, 2, (100,200), ("left","left"), parent=self.account_settings_frame) as threadsRow:
            self.account_ui_elements.append(threadsRow)
            maya.text(label="Threads:    ", align="left")
            self._threads = maya.int_field(
                changeCommand=self.set_threads,
                height=25,
                minValue=1,
                maxValue=40,
                enable=True,
                value=self.base.threads)
            
        with utils.Row(2, 2, (100,200), ("left","center"),
                        [(1, "bottom", 20),(2,"bottom",15)], parent=self.account_settings_frame) as loggingRow:
            self.account_ui_elements.append(loggingRow)
            maya.text(label="Logging:    ", align="left")
            with utils.Dropdown(self.set_logging) as log_settings:
                self._logging = log_settings
                self._logging.add_item("Debug")
                self._logging.add_item("Info")
                self._logging.add_item("Warning")
                self._logging.add_item("Error")
        maya.form_layout(self.page, edit=True, enable=True)
        maya.refresh()

    def init_from_config(self):
        maya.delete_ui(self.auth_layout)
        self.subscription_ui_elements = []
        with utils.ScrollLayout(height=520, parent=self.page, width=375) as scroll:
            box_label = "Batch Account Settings"
            with utils.FrameLayout(label=box_label, collapsable=True, width=325) as account_settings_frame:
                self.account_settings_frame = account_settings_frame
                with utils.Row(1, 1, (300), ("left"), [(1, "top", 15)], parent=self.account_settings_frame):
                    self.auth_status = maya.text(label="", align="center")

                with utils.Row(3, 3, (100, 170, 30), ("left","left", "left"),  parent=self.account_settings_frame) as subscriptionRow:
                    maya.text(label="Subscription:    ", align="left")
                    with utils.Dropdown(self.select_subscription_in_dropdown, enable=False) as subscription_dropdown:
                        self._subscription_dropdown = subscription_dropdown
                        self.subscription_ui_elements.append(self._subscription_dropdown)
                        self._subscription_dropdown.add_item(self.base.subscription_name)
                    
                    self._change_subscription_button = maya.button(label="Change", command=self.change_subscription_button_pressed, width=30)
                    self.subscription_row = subscriptionRow

                with utils.Row(3, 3, (100, 170, 30), ("left","left", "left"), parent=self.account_settings_frame) as batch_account_row:
                    maya.text(label="Batch Account:    ", align="left")
                    maya.refresh()
                    with utils.Dropdown(self.select_account_in_dropdown, enable=False) as account_dropdown:
                        self._account_dropdown = account_dropdown
                        self._account_dropdown.add_item(self.base.batch_account)
                    
                    self._change_batch_account_button = maya.button(label="Change", command=self.change_batch_account_button_pressed, width=30)
                    self.batch_account_row = batch_account_row

                #TODO test the case that autostorage is removed from a stored account in config
                self.account_ui_elements = []
                with utils.Row(2, 2, (100, 200), ("left","left"),[(1, "bottom", 20),(2,"bottom",15)], parent=self.account_settings_frame) as storageAccountRow:
                    self.account_ui_elements.append(storageAccountRow)
                    maya.text(label="Storage Account:", align="left")
                    self.storage_account_field = maya.text_field(height=25, enable=True, editable=False, text=self.base.storage_account)

                #TODO: Allow set to 0 to disable threads
                with utils.Row(2, 2, (100,200), ("left","left"), parent=self.account_settings_frame) as threadsRow:
                    self.account_ui_elements.append(threadsRow)
                    maya.text(label="Threads:    ", align="left")
                    self._threads = maya.int_field(
                        changeCommand=self.set_threads,
                        height=25,
                        minValue=1,
                        maxValue=40,
                        enable=True,
                        value=self.base.threads)
            
                with utils.Row(2, 2, (100,200), ("left","center"),
                                [(1, "bottom", 20),(2,"bottom",15)], parent=self.account_settings_frame) as loggingRow:
                    self.account_ui_elements.append(loggingRow)
                    maya.text(label="Logging:    ", align="left")
                    with utils.Dropdown(self.set_logging) as log_settings:
                        self._logging = log_settings
                        self._logging.add_item("Debug")
                        self._logging.add_item("Info")
                        self._logging.add_item("Warning")
                        self._logging.add_item("Error")

        self.status = "Authenticated"
        self.disable(True)
        maya.form_layout(self.page, edit=True, enable=True)
        maya.refresh()

    def init_post_auth(self):
        maya.delete_ui(self.auth_layout)
        if self.subscription_ui_elements is not None and not len(self.subscription_ui_elements) == 0:
            maya.delete_ui(self.subscription_ui_elements)
        if self.subscription_row is not None:
            maya.delete_ui(self.subscription_row)
        if self.batch_account_row is not None:
            maya.delete_ui(self.batch_account_row)
        if self.account_ui_elements:
            maya.delete_ui(self.account_ui_elements)
        self.account_ui_elements = []
        self.subscription_ui_elements = []
        with utils.ScrollLayout(height=520, parent=self.page, width=325) as scroll:
            box_label = "Batch Account Settings"
            with utils.FrameLayout(label=box_label, collapsable=True) as account_settings_frame:
                self.account_settings_frame = account_settings_frame
                with utils.Row(1, 1, (300), ("left"), [(1, "top", 15)]):
                    self.auth_status = maya.text(label="", align="center")
                    self.status = "Please select Subscription"
                with utils.Row(2, 2, (100,200), ("left","left")) as subscriptionRow:
                    self.subscription_row = subscriptionRow
                    maya.text(label="Subscription:    ", align="left")
                    with utils.Dropdown(self.select_subscription_in_dropdown) as subscription_dropdown:
                        self._subscription_dropdown = subscription_dropdown
                        self._subscription_dropdown.add_item("")
                        self.subscription_ui_elements.append(self._subscription_dropdown)
                        
                        subscriptions = self.base.available_subscriptions()
                        self.subscriptions_by_displayname = dict([ (sub.display_name, sub) for sub in subscriptions ])
                        for sub in subscriptions:
                            self._subscription_dropdown.add_item(sub.display_name)

                 #TODO: Allow set to 0 to disable threads
                with utils.Row(2, 2, (100,200), ("left","left"), parent=self.account_settings_frame) as threadsRow:
                    self.account_ui_elements.append(threadsRow)
                    maya.text(label="Threads:    ", align="left")
                    self._threads = maya.int_field(
                        changeCommand=self.set_threads,
                        height=25,
                        minValue=1,
                        maxValue=40,
                        enable=True,
                        value=self.base.threads)
            
                with utils.Row(2, 2, (100,200), ("left","center"),
                                [(1, "bottom", 20),(2,"bottom",15)], parent=self.account_settings_frame) as loggingRow:
                    self.account_ui_elements.append(loggingRow)
                    maya.text(label="Logging:    ", align="left")
                    with utils.Dropdown(self.set_logging) as log_settings:
                        self._logging = log_settings
                        self._logging.add_item("Debug")
                        self._logging.add_item("Info")
                        self._logging.add_item("Warning")
                        self._logging.add_item("Error")

        self.disable(True)
        maya.form_layout(self.page, edit=True, enable=True)
        maya.refresh()

    def init_after_subscription_selected(self):
        self.status = "Loading"
        maya.refresh()
        if self.batch_account_row is not None:
            maya.delete_ui(self.batch_account_row)
        if self.account_ui_elements:
            maya.delete_ui(self.account_ui_elements)
        self.disable(False)
        self.account_ui_elements = []
        with utils.Row(2, 2, (100,200), ("left","left"), parent=self.account_settings_frame) as batch_account_row:
            self.batch_account_row = batch_account_row
            maya.text(label="Batch Account:    ", align="left")
            with utils.Dropdown(self.select_account_in_dropdown) as account_dropdown:
                self._account_dropdown = account_dropdown
                self._account_dropdown.add_item("")
                accounts = self.base.available_batch_accounts()
                self.accounts_by_name = dict([ (account.name, account) for account in accounts ])
                for account in accounts:
                    self._account_dropdown.add_item(account.name)
        self.status = "Please select Batch Account"

        with utils.Row(2, 2, (100,200), ("left","left"), parent=self.account_settings_frame) as threadsRow:
            self.account_ui_elements.append(threadsRow)
            maya.text(label="Threads:    ", align="left")
            self._threads = maya.int_field(
                changeCommand=self.set_threads,
                height=25,
                minValue=1,
                maxValue=40,
                enable=True,
                value=self.base.threads)

        with utils.Row(2, 2, (100,200), ("left","center"),
                        [(1, "bottom", 20),(2,"bottom",15)], parent=self.account_settings_frame) as loggingRow:
            self.account_ui_elements.append(loggingRow)
            maya.text(label="Logging:    ", align="left")
            with utils.Dropdown(self.set_logging) as log_settings:
                self._logging = log_settings
                self._logging.add_item("Debug") 
                self._logging.add_item("Info")
                self._logging.add_item("Warning")
                self._logging.add_item("Error")
        self.disable(True)
        maya.refresh()

    def init_after_batch_account_selected(self):
        if self.account_ui_elements:
            maya.delete_ui(self.account_ui_elements)
        self.account_ui_elements = []
        self.status = "Authenticated"
        with utils.Row(2, 2, (100, 200), ("left","left"),[(1, "bottom", 20),(2,"bottom",15)], parent=self.account_settings_frame) as storageAccountRow:
            self.account_ui_elements.append(storageAccountRow)
            maya.text(label="Storage Account:", align="left")
            self.storage_account_field = maya.text_field(height=25, enable=True, editable=False, text=self.base.storage_account)

        #TODO: Allow set to 0 to disable threads
        with utils.Row(2, 2, (100,200), ("left","left"), parent=self.account_settings_frame) as threadsRow:
            self.account_ui_elements.append(threadsRow)
            maya.text(label="Threads:    ", align="left")
            self._threads = maya.int_field(
                changeCommand=self.set_threads,
                height=25,
                minValue=1,
                maxValue=40,
                enable=True,
                value=self.base.threads)
            
        with utils.Row(2, 2, (100,200), ("left","center"),
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

    def select_subscription_in_dropdown(self, selected_subscription_name):
        self.status = "Loading"
        maya.refresh()
        if selected_subscription_name:
            self._subscription_dropdown.select(selected_subscription_name)
        else:
            self._subscription_dropdown.select(2)
            selected_subscription_name =  self._subscription_dropdown.value()
        self.base.subscription_id = self.subscriptions_by_displayname[selected_subscription_name].subscription_id
        self.subscription = selected_subscription_name
        self.base.init_after_subscription_selected(self.base.subscription_id, selected_subscription_name)
        self.init_after_subscription_selected()

    def select_account_in_dropdown(self, account_displayName):
        self.status = "Loading"
        maya.refresh()
        if account_displayName:
            self._account_dropdown.select(account_displayName)
        else:
            self._account_dropdown.select(2)
            account_displayName = self._account_dropdown.value()
        self.selected_batchaccount = self.accounts_by_name[account_displayName]
        self.base.init_after_batch_account_selected(self.selected_batchaccount, self.base.subscription_id)
        self.init_after_batch_account_selected()

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
    def status(self):
        """Plug-in authentication status. Sets contents of label."""
        return maya.text(self.auth_status, query=True, label=True)[8:]

    @status.setter
    def status(self, value):
        """Plug-in authentication status. Sets contents of label."""
        if value == "Authenticated":
            maya.text(self.auth_status, edit=True, label="Authenticated", backgroundColor=[0.23, 0.44, 0.21])
        else:
            if value == "Loading":
                maya.text(self.auth_status, edit=True, label="Loading", backgroundColor=[0.6, 0.23, 0.23])
            else:
                maya.text(self.auth_status, edit=True, label=value, backgroundColor=[0.6, 0.6, 0.23])

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
       
        #cut out the login code from the middle of the string and construct our own string, to include the hyperlink
        self.devicelogin_code = value.split("and enter the code ",1)[1][:9]
        login_prompt_string = "To sign in, use a web browser to open the page <a href=\"https://aka.ms/devicelogin/\">https://aka.ms/devicelogin</a> and enter the code {} to authenticate."
        login_prompt_string = login_prompt_string.format(self.devicelogin_code)

        maya.text(self.heading, edit=True, label=login_prompt_string, align="center", font="plainLabelFont", hyperlink=True, parent=self.auth_layout, backgroundColor=[0.75, 0.75, 0.75], width=300)
        maya.button(label="Copy Code to clipboard", command=self.copy_devicelogincode_to_clipboard, parent=self.auth_layout, width=200)
        maya.form_layout(self.page, edit=True, enable=True)

    def copy_devicelogincode_to_clipboard(self, *args):
        utils.copy_to_clipboard(self.devicelogin_code.rstrip())

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

    def authenticate(self, *args):
        """Initiate plug-in authentication, and save updated credentials
        to the config file.
        """
        self.base.save_changes()
        self.base.authenticate()
    
    def disable(self, enabled): #TODO rename to enable
        """Disable the tab from user interaction. Used during long running
        processes like upload, and when plug-in is unauthenticated.
        :param bool enabled: Whether to enable the display. False will
         disable the display.
        """
        maya.form_layout(self.page, edit=True, enable=enabled)