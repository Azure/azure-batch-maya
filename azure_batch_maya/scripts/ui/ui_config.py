# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import azurebatchutils as utils

from azurebatchmayaapi import MayaAPI as maya
from adal import AdalError


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
        self.auth_temp_ui_elements = []
        self.batch_account_framelayout = None

        with utils.ScrollLayout(height=475, width = 375, parent = self.page) as scroll_layout:
            self.scroll_layout = scroll_layout
            self.heading = maya.text(label="Loading plug-in...", align="center", font="boldLabelFont", wordWrap=True)
           
        frame.add_tab(self)
        maya.form_layout(self.page, edit=True, enable=False)
        maya.refresh()

    def init_post_config_file_read(self):
        maya.delete_ui(self.heading)
        self.heading = None
        box_label = "AzureActiveDirectory Authentication"
        with utils.FrameLayout(label=box_label, collapsable=True, width=345, collapse=False, parent = self.scroll_layout) as aad_framelayout:
            self.aad_framelayout = aad_framelayout
        with utils.Row(1, 1, (300), ("left"), [(1, "top", 15)], parent=self.aad_framelayout):
            self.auth_status_field = maya.text(label="", align="center")
        with utils.Row(2, 2, (75,255), ("right","center"), [(1, "bottom", 20),(2,"bottom",15)], parent = self.aad_framelayout) as aad_tenant_row:
            self.aad_tenant_row = aad_tenant_row
            maya.text(label="AAD Tenant:   ", align="left", parent = self.aad_tenant_row)
            self._aad_tenant_field = maya.text_field(height=25, enable=True,
                changeCommand=self.aad_tenant_name_changed,
                annotation="Please input your AAD tenant name, e.g. 'microsoft.onmicrosoft.com'",
                parent = self.aad_tenant_row)

        maya.form_layout(self.page, edit= True, enable=False, 
            attachForm=[(self.scroll_layout, 'top', 5), (self.scroll_layout, 'left', 5),
                        (self.scroll_layout, 'right', 5)])

        cached_tenant_name =  self.base.aad_tenant_name
        if cached_tenant_name and cached_tenant_name != None and cached_tenant_name != 'None':
            maya.text_field(self._aad_tenant_field, edit=True, text=cached_tenant_name)

    def prompt_for_aad_tenant(self):
        self.auth_status = "Please input your AAD tenant name"
        maya.form_layout(self.page, edit=True, enable=True)
        maya.refresh() 

    def prompt_for_login(self, original_prompt_message):
        """Called when we need to prompt for 'devicelogin' signin to AAD through display of logincode and href.

        :param str original_prompt_message: The original sign in prompt message returned from the AAD library, from which we parse the logincode.
        """
        login_prompt_string = self.build_signin_prompt_string(original_prompt_message)

        maya.delete_ui(self.auth_temp_ui_elements)
        self.auth_temp_ui_elements = []
        self.auth_temp_ui_elements.append(maya.text(label=login_prompt_string, align="center", font="plainLabelFont", hyperlink=True, backgroundColor=[0.75, 0.75, 0.75], width=300, wordWrap=True, parent=self.aad_framelayout))
        self.auth_temp_ui_elements.append(maya.button(label="Copy Code to clipboard", command=self.copy_devicelogincode_to_clipboard, width=200, parent=self.aad_framelayout))
        maya.form_layout(self.page, edit=True, enable=True)

    def build_signin_prompt_string(self, original_prompt_message):
        #cut out the login code from the middle of the string and construct our own string, to include the hyperlink
        self.devicelogin_code = original_prompt_message.split("and enter the code ",1)[1][:9]
        login_prompt_string = "To sign in, use a web browser to open the page <a href=\"https://aka.ms/devicelogin/\">https://aka.ms/devicelogin</a> and enter the code {} to authenticate."
        login_prompt_string = login_prompt_string.format(self.devicelogin_code)
        return login_prompt_string

    def init_from_config(self):
        maya.delete_ui(self.auth_temp_ui_elements)
        self.subscription_ui_elements = []
        box_label = "Batch Account Settings"
        with utils.FrameLayout(label=box_label, collapsable=True, width=345, collapse=False, parent = self.scroll_layout) as batch_account_framelayout:
            self.batch_account_framelayout = batch_account_framelayout
            with utils.Row(1, 1, (300), ("left"), [(1, "top", 15)], parent=self.batch_account_framelayout):
                self.account_status_field = maya.text(label="", align="center")
                self.account_status = maya.text(label="", align="center")

            with utils.Row(3, 3, (100, 170, 30), ("left","left", "left"),  parent=self.batch_account_framelayout) as subscriptionRow:
                maya.text(label="Subscription:    ", align="left")
                with utils.Dropdown(self.select_subscription_in_dropdown, enable=False) as subscription_dropdown:
                    self._subscription_dropdown = subscription_dropdown
                    self.subscription_ui_elements.append(self._subscription_dropdown)
                    self._subscription_dropdown.add_item(self.base.subscription_name)
                    
                self._change_subscription_button = maya.button(label="Change", command=self.change_subscription_button_pressed, width=30)
                self.subscription_row = subscriptionRow

            with utils.Row(3, 3, (100, 170, 30), ("left","left", "left"), parent=self.batch_account_framelayout) as batch_account_row:
                maya.text(label="Batch Account:    ", align="left")
                maya.refresh()
                with utils.Dropdown(self.select_account_in_dropdown, enable=False) as account_dropdown:
                    self._account_dropdown = account_dropdown
                    self._account_dropdown.add_item(self.base.batch_account)
                    
                self._change_batch_account_button = maya.button(label="Change", command=self.change_batch_account_button_pressed, width=30)
                self.batch_account_row = batch_account_row

            #TODO test the case that autostorage is removed from a stored account in config
            self.account_ui_elements = []
            with utils.Row(2, 2, (100, 200), ("left","left"),[(1, "bottom", 20),(2,"bottom",15)], parent=self.batch_account_framelayout) as storageAccountRow:
                self.account_ui_elements.append(storageAccountRow)
                maya.text(label="Storage Account:", align="left")
                self.storage_account_field = maya.text_field(height=25, enable=True, editable=False, text=self.base.storage_account)

            #TODO: Allow set to 0 to disable threads
            with utils.Row(2, 2, (100,200), ("left","left"), parent=self.batch_account_framelayout) as threadsRow:
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
                            [(1, "bottom", 20),(2,"bottom",15)], parent=self.batch_account_framelayout) as loggingRow:
                self.account_ui_elements.append(loggingRow)
                maya.text(label="Logging:    ", align="left")
                with utils.Dropdown(self.set_logging) as log_settings:
                    self._logging = log_settings
                    self._logging.add_item("Debug")
                    self._logging.add_item("Info")
                    self._logging.add_item("Warning")
                    self._logging.add_item("Error")

        self.account_status = "Batch Account Configured"
        self.auth_status = "Authenticated"
        self.disable(True)
        maya.form_layout(self.page, edit=True, enable=True)
        maya.refresh()

    def init_post_auth(self):
        maya.delete_ui(self.auth_temp_ui_elements)
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

        box_label = "Batch Account Settings"
        with utils.FrameLayout(label=box_label, collapsable=True, width=345, collapse=False, parent = self.scroll_layout) as batch_account_framelayout:
            self.batch_account_framelayout = batch_account_framelayout
            with utils.Row(1, 1, (300), ("left"), [(1, "top", 15)]):
                self.account_status_field = maya.text(label="", align="center")
                self.account_status = "Please select Subscription"
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
            with utils.Row(2, 2, (100,200), ("left","left"), parent=self.batch_account_framelayout) as threadsRow:
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
                            [(1, "bottom", 20),(2,"bottom",15)], parent=self.batch_account_framelayout) as loggingRow:
                self.account_ui_elements.append(loggingRow)
                maya.text(label="Logging:    ", align="left")
                with utils.Dropdown(self.set_logging) as log_settings:
                    self._logging = log_settings
                    self._logging.add_item("Debug")
                    self._logging.add_item("Info")
                    self._logging.add_item("Warning")
                    self._logging.add_item("Error")

        self.auth_status = "Authenticated"
        self.disable(True)
        maya.form_layout(self.page, edit=True, enable=True)
        maya.refresh()

    def change_subscription_button_pressed(self, *args):
        self.account_status = "Loading"
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
        self.account_status = "Please select Subscription"

        #TODO: Allow set to 0 to disable threads
        with utils.Row(2, 2, (100,200), ("left","left"), parent=self.batch_account_framelayout) as threadsRow:
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
                        [(1, "bottom", 20),(2,"bottom",15)], parent=self.batch_account_framelayout) as loggingRow:
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
        self.account_status = "Loading"
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
        self.account_status = "Account Configured"

        #TODO: Allow set to 0 to disable threads
        with utils.Row(2, 2, (100,200), ("left","left"), parent=self.batch_account_framelayout) as threadsRow:
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
                        [(1, "bottom", 20),(2,"bottom",15)], parent=self.batch_account_framelayout) as loggingRow:
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

    def init_after_subscription_selected(self):
        self.account_status = "Loading"
        maya.refresh()
        if self.batch_account_row is not None:
            maya.delete_ui(self.batch_account_row)
        if self.account_ui_elements:
            maya.delete_ui(self.account_ui_elements)
        self.disable(False)
        self.account_ui_elements = []
        with utils.Row(2, 2, (100,200), ("left","left"), parent=self.batch_account_framelayout) as batch_account_row:
            self.batch_account_row = batch_account_row
            maya.text(label="Batch Account:    ", align="left")
            with utils.Dropdown(self.select_account_in_dropdown) as account_dropdown:
                self._account_dropdown = account_dropdown
                self._account_dropdown.add_item("")
                accounts = self.base.available_batch_accounts()
                self.accounts_by_name = dict([ (account.name, account) for account in accounts ])
                for account in accounts:
                    self._account_dropdown.add_item(account.name)
        self.account_status = "Please select Batch Account"

        with utils.Row(2, 2, (100,200), ("left","left"), parent=self.batch_account_framelayout) as threadsRow:
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
                        [(1, "bottom", 20),(2,"bottom",15)], parent=self.batch_account_framelayout) as loggingRow:
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
        self.account_status = "Batch Account Configured"
        with utils.Row(2, 2, (100, 200), ("left","left"),[(1, "bottom", 20),(2,"bottom",15)], parent=self.batch_account_framelayout) as storageAccountRow:
            self.account_ui_elements.append(storageAccountRow)
            maya.text(label="Storage Account:", align="left")
            self.storage_account_field = maya.text_field(height=25, enable=True, editable=False, text=self.base.storage_account)

        #TODO: Allow set to 0 to disable threads
        with utils.Row(2, 2, (100,200), ("left","left"), parent=self.batch_account_framelayout) as threadsRow:
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
                        [(1, "bottom", 20),(2,"bottom",15)], parent=self.batch_account_framelayout) as loggingRow:
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
        self.account_status = "Loading"
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
        self.account_status = "Loading"
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
    def account_status(self):
        """Batch account configuration status. Gets contents of label."""
        return maya.text(self.account_status_field, query=True, label=True)[8:]

    @account_status.setter
    def account_status(self, value):
        """Batch account configuration status. Sets contents of label."""
        if value == "Batch Account Configured":
            maya.text(self.account_status_field, edit=True, label="Batch Account Configured", backgroundColor=[0.23, 0.44, 0.21])
        else:
            if value == "Loading":
                maya.text(self.account_status_field, edit=True, label="Loading", backgroundColor=[0.6, 0.23, 0.23])
            else:
                maya.text(self.account_status_field, edit=True, label=value, backgroundColor=[0.6, 0.6, 0.23])

    @property
    def auth_status(self):
        """Plug-in authentication status. Gets contents of label."""
        return maya.text(self.auth_status_field, query=True, label=True)[8:]

    @auth_status.setter
    def auth_status(self, value):
        """Plug-in authentication status. Sets contents of label."""
        if value == "Authenticated":
            maya.text(self.auth_status_field, edit=True, label="Authenticated", backgroundColor=[0.23, 0.44, 0.21])
        else:
            if value == "Loading":
                maya.text(self.auth_status_field, edit=True, label="Loading", backgroundColor=[0.6, 0.23, 0.23])
            else:
                if value == "AAD Tenant not found or contains no subscriptions":
                    maya.text(self.auth_status_field, edit=True, label="AAD Tenant not found or contains no subscriptions", backgroundColor=[0.9, 0.23, 0.23])
                else:
                    maya.text(self.auth_status_field, edit=True, label=value, backgroundColor=[0.6, 0.6, 0.23])

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
        """Called when the plug-in is authenticated."""
        maya.form_layout(self.page, edit=True, enable=True)

    def is_logged_out(self):
        """Called when the plug-in is logged out."""
        maya.form_layout(self.page, edit=True, enable=True)

    def aad_tenant_name_changed(self, aad_tenant_name):
        if aad_tenant_name != None:
            self.base.aad_tenant_name = aad_tenant_name

            if self.batch_account_framelayout is not None:
                maya.delete_ui(self.batch_account_framelayout)
            
            if self.auth_temp_ui_elements is not None:
                maya.delete_ui(self.auth_temp_ui_elements)
            self.auth_temp_ui_elements = []

            self.base.can_init_from_config = False
            self.base.auth = False
            self.base.session()
            #self.frame.is_logged_out()

            try:
                self.base.obtain_aad_tokens()
                self.auth_status = "Please follow instructions below to sign in."
                maya.refresh()
            except AdalError as exp:
                errors = exp.error_response['error_codes']
                if 90002 in errors:
                    self.auth_status = "AAD Tenant not found or contains no subscriptions"
                    maya.refresh()

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
