# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import ConfigParser
import os
import json
import datetime
import logging
import sys
import traceback
import adal
import maya.utils

from Queue import Queue

import threading
from ui_config import ConfigUI
from azurebatchmayaapi import MayaAPI as maya
from dateutil.parser import parse as dateparse

import azure.storage.blob as storage
import azure.batch_extensions as batch
from azure.mgmt.resource.subscriptions import SubscriptionClient
from azure.mgmt.batch import BatchManagementClient
from azure.mgmt.storage import StorageManagementClient

from azure.batch.batch_auth import SharedKeyCredentials
from msrestazure.azure_active_directory import AdalAuthentication
from msrestazure.azure_active_directory import AADTokenCredentials
import msrestazure.tools as msrestazuretools


LOG_LEVELS = {
    'debug':10,
    'info':20,
    'warning':30,
    'error':40}


class AzureBatchConfig(object):
    """Handler for authentication and configuration of the SDK clients."""

    batchAadResource = "https://batch.core.windows.net/"
    mgmtAadResource = "https://management.core.windows.net/"
    aadTenant = "microsoft.onmicrosoft.com"
    aadAuthorityHostUrl = "https://login.microsoftonline.com"
    aadClientId = "72d009d6-c30b-4728-9222-bb4cf6ca393c"

    def __init__(self, index, settings, frame, start, call):
        """Create new configuration Handler.

        :param index: The UI tab index.
        :param frame: The shared plug-in UI frame.
        :type frame: :class:`.AzureBatchUI`
        :param func call: The shared REST API call wrapper.
        """
        self.ui = None
        self.session = start
        self._tab_index = index
        self._data_dir = os.path.join(maya.prefs_dir(), 'AzureBatchData')
        self._ini_file = "azure_batch.ini"
        self._user_agent = "batchmaya/{}".format(os.environ.get('AZUREBATCH_VERSION'))
        self._cfg = ConfigParser.ConfigParser()
        self._client = None
        self._log = None
        self._storage = None
        self._credentials = None
        self._call = call
        self.ui = ConfigUI(self, settings, frame)
        self._configure_plugin(False)

    @property
    def batch(self):
        return self._client

    @property
    def subscription_client(self):
        return self._subscription_client

    @subscription_client.setter
    def subscription_client(self, value):
        self._subscription_client = value

    @property
    def storage(self):
        return self._storage

    @property
    def batch_auth_token(self):
        return self._batch_auth_token

    @batch_auth_token.setter
    def batch_auth_token(self, value):
        self._batch_auth_token = value

    @property
    def mgmt_auth_token(self):
        return self._mgmt_auth_token

    @mgmt_auth_token.setter
    def mgmt_auth_token(self, value):
        self._mgmt_auth_token = value

    @property
    def auth(self):
        return self._auth

    @property
    def path(self):
        return os.path.join(self._data_dir, self._ini_file)

    def _configure_plugin(self, from_auth_button):
        """Set up the the config file, authenticate the SDK clients
        and set up the log file.
        """
        if not os.path.exists(self._data_dir):
            os.makedirs(self._data_dir)
        config_file = os.path.join(self._data_dir, self._ini_file)
        if not os.path.exists(config_file):
            self._log = self._configure_logging(LOG_LEVELS['debug'])
            return
        try:
            self._cfg.read(config_file)

            self.ui.disable(True)

            self._read_config_file()

        except Exception as exp:
            # We should only worry about this if it happens when authenticating
            # using the UI, otherwise it's expected.
            if from_auth_button:
                raise ValueError("Invalid Configuration: {}".format(exp))
            else:
                # We'll need a place holder logger
                self._log = self._configure_logging(LOG_LEVELS['debug'])

        if(not self.mgmt_auth_token or not self.batch_auth_token):
            self.obtain_aad_tokens()
        else:
            if self.need_to_refresh_auth_tokens([self.mgmt_auth_token, self.batch_auth_token]):
                self.refresh_auth_tokens(self.mgmt_auth_token, self.batch_auth_token)

        self.mgmtCredentials = AADTokenCredentials(self.mgmt_auth_token)
        self.batchCredentials = AADTokenCredentials(self.batch_auth_token)

        self.store_mgmt_auth_token(self.mgmt_auth_token)
        self.store_batch_auth_token(self.batch_auth_token)

        self.subscription_client = SubscriptionClient(self.mgmtCredentials)

        self.ui.init_post_auth()

    def _configure_batch_client(self):
        self._client = batch.BatchExtensionsClient(
            batchCredentials, base_url=self._cfg.get('AzureBatch', 'batch_url'),
            storage_client=self._storage)

        self._client.config.add_user_agent(self._user_agent)
        self._log = self._configure_logging(
            self._cfg.get('AzureBatch', 'logging'))
        self._auth = self._auto_authentication()

        self._storage = storage.BlockBlobService(
                self._cfg.get('AzureBatch', 'storage_account'),
                self._cfg.get('AzureBatch', 'storage_key'))

        self._storage.MAX_SINGLE_PUT_SIZE = 2 * 1024 * 1024

    def need_to_refresh_auth_tokens(self, auth_token_list):

        currentTimeUtc = datetime.datetime.utcnow()

        tokenRefreshThresholdSeconds = 5 * 60

        for token in auth_token_list:
            if (dateparse(token['expiresOn']) - currentTimeUtc).total_seconds() < tokenRefreshThresholdSeconds:
                return True
        return False

    def refresh_auth_tokens(self, mgmt_token, batch_token):

        context = adal.AuthenticationContext(self.aadAuthorityHostUrl + '/' + self.aadTenant, api_version=None)

        self.mgmt_auth_token = context.acquire_token_with_refresh_token(
            mgmt_token['refreshToken'],
            self.aadClientId,
            self.mgmtAadResource)

        self.batch_auth_token =  context.acquire_token_with_refresh_token(
            batch_token['refreshToken'],
            self.aadClientId,
            self.batchAadResource)

    def obtain_aad_tokens(self):

        context = adal.AuthenticationContext(self.aadAuthorityHostUrl + '/' + self.aadTenant, api_version=None)

        code = context.acquire_user_code(self.batchAadResource, self.aadClientId)

        self.ui.prompt_for_login(code['message'])
        maya.refresh()
        self.ui.disable(False)

        def aad_auth_thread_func(context, code):
            self.mgmt_auth_token = context.acquire_token_with_device_code(self.mgmtAadResource, code, self.aadClientId)
            self.batch_auth_token = context.acquire_token(self.batchAadResource, self.mgmt_auth_token['userId'], self.aadClientId)
            maya.execute_in_main_thread(self._configure_post_auth)

        authThread = threading.Thread(
            target=aad_auth_thread_func,
            args=(context, code))

        authThread.start()

    def _configure_logging(self, log_level):
        """Configure the logger. Setup the file output and format
        the log messages.

        :param log_level: The specified level of logging verbosity.
        """
        level = int(log_level)
        logger = logging.getLogger('AzureBatchMaya')
        file_format = logging.Formatter(
            "%(asctime)-15s [%(levelname)s] %(module)s: %(message)s")
        logfile = os.path.join(self._data_dir, "azure_batch.log")
        if not os.path.exists(logfile):
            with open(logfile, 'w') as handle:
                handle.write("Azure Batch Plugin Log")
        file_logging = logging.FileHandler(logfile)
        file_logging.setFormatter(file_format)
        logger.addHandler(file_logging)
        logger.setLevel(level)
        return logger

    def _read_config_file(self):
        """Populate the config tab UI with the values loaded from the
        configuration file.
        """
        try:
            self._cfg.add_section('AzureBatch')
        except ConfigParser.DuplicateSectionError:
            pass
        try:
            self._batch_auth_token = json.loads(self._cfg.get('AzureBatch', 'batch_auth_token'))
        except ConfigParser.NoOptionError:
            self._batch_auth_token = ""
        try:
            self._mgmt_auth_token = json.loads(self._cfg.get('AzureBatch', 'mgmt_auth_token'))
        except ConfigParser.NoOptionError:
            self._mgmt_auth_token = ""
        try:
            self._subscription_id = self._cfg.get('AzureBatch', 'subscription_id')
        except ConfigParser.NoOptionError:
            self._subscription_id = ""
        try:
            self.ui.endpoint = self._cfg.get('AzureBatch', 'batch_url')
        except ConfigParser.NoOptionError:
            self.ui.endpoint = ""
        try:
            self.ui.account = self._cfg.get('AzureBatch', 'batch_account')
        except ConfigParser.NoOptionError:
            self.ui.account = ""
        try:
            self.ui.storage = self._cfg.get('AzureBatch', 'storage_account')
        except ConfigParser.NoOptionError:
            self.ui.storage = ""
        try:
            self.ui.storage_key = self._cfg.get('AzureBatch', 'storage_key')
        except ConfigParser.NoOptionError:
            self.ui.storage_key = ""
        try:
            self.ui.logging = self._cfg.getint('AzureBatch', 'logging')
        except ConfigParser.NoOptionError:
            self.ui.logging = 10
        try:
            self.ui.threads = self._cfg.getint('AzureBatch', 'threads')
        except ConfigParser.NoOptionError:
            self.ui.threads = 20
        finally:
            if self._client != None:
                self._client.threads = self.ui.threads
        self.ui.set_authenticate(self._auth)

    def _auto_authentication(self):
        """Test whether the clients are correctly authenticated
        by doing some quick API calls.
        """
        try:
            filter = batch.models.PoolListOptions(max_results=1, select="id")
            list(self._client.pool.list(filter))
            self._storage.list_containers(num_results=1)
            return True
        except Exception as exp:
            self._log.info("Failed to authenticate: {0}".format(exp))
            return False

    def _save_config(self):
        """Persist the current plugin configuration to file."""
        config_file = os.path.join(self._data_dir, self._ini_file)
        with open(config_file, 'w') as handle:
            self._cfg.write(handle)

    def set_logging(self, level):
        """Set the logging level to that specified in the UI.
        :param str level: The specified logging level.
        """
        self._log.setLevel(level)
        self._cfg.set('AzureBatch', 'logging', level)
        self._save_config()

    def set_threads(self, threads):
        """Set the number of threads to that specified in the UI.
        :param int threads: The specified number of threads.
        """
        self._cfg.set('AzureBatch', 'threads', threads)
        self._client.threads = threads
        self._save_config()

    def save_changes(self):
        """Persist auth config changes to file for future sessions."""
        try:
            self._cfg.add_section('AzureBatch')
        except ConfigParser.DuplicateSectionError:
            pass
        self._cfg.set('AzureBatch', 'batch_url', self.batch_url)
        self._cfg.set('AzureBatch', 'batch_account', self.batch_account)
        self._cfg.set('AzureBatch', 'storage_account', self.storage_account)
        self._cfg.set('AzureBatch', 'storage_key', self.storage_key)
        self._cfg.set('AzureBatch', 'mgmt_auth_token', json.dumps(self.mgmt_auth_token))
        self._cfg.set('AzureBatch', 'batch_auth_token', json.dumps(self.batch_auth_token))
        self._save_config()

    def authenticate(self):
        """Begin authentication - initiated by the UI button."""
        try:
            self._configure_plugin(True)
            self._auth = self._auto_authentication()
        except ValueError as exp:
            maya.error(str(exp))
            self._auth = False
        finally:
            self.ui.set_authenticate(self._auth)
            self.session()
    
    def get_threads(self):
        """Attempt to retrieve number of threads configured for the plugin."""
        return self._client.threads

    def get_cached_vm_sku(self):
        """Attempt to retrieve a selected VM SKU from a previous session."""
        try:
            return self._cfg.get('AzureBatch', 'vm_sku')
        except ConfigParser.NoOptionError:
            return None

    def store_vm_sku(self, sku):
        """Cache selected VM SKU for later sessions."""
        self._cfg.set('AzureBatch', 'vm_sku', sku)
        self._save_config()

    def get_cached_image(self):
        """Attempt to retrieve a selected image a previous session."""
        try:
            return self._cfg.get('AzureBatch', 'image')
        except ConfigParser.NoOptionError:
            return None

    def store_image(self, image):
        """Cache selected image for later sessions."""
        self._cfg.set('AzureBatch', 'image', image)
        self._save_config()

    def store_mgmt_auth_token(self, mgmt_auth_token):
        """Cache selected image for later sessions."""
        self._cfg.set('AzureBatch', 'mgmt_auth_token', json.dumps(mgmt_auth_token))
        self._save_config()
    
    def store_batch_auth_token(self, batch_auth_token):
        """Cache selected image for later sessions."""
        self._cfg.set('AzureBatch', 'batch_auth_token', json.dumps(batch_auth_token))
        self._save_config()

    def get_cached_subscription(self):
        """Attempt to retrieve a selected subscription from a previous session."""
        try:
            return self._cfg.get('AzureBatch', 'subscription')
        except ConfigParser.NoOptionError:
            return None

    def store_subscription(self, subscription):
        """Cache selected subscription for later sessions."""
        self._cfg.set('AzureBatch', 'subscription', subscription)
        self._save_config()

    def get_cached_batch_account(self):
        """Attempt to retrieve a selected batch account from a previous session."""
        try:
            return self._cfg.get('AzureBatch', 'subscription')
        except ConfigParser.NoOptionError:
            return None

    def store_batch_account(self, batch_account):
        """Cache selected batch account for later sessions."""
        self._cfg.set('AzureBatch', 'batch_account', batch_account)
        self._save_config()

    def get_cached_autoscale_formula(self):
        """Attempt to retrieve an autoscale forumla from a previous session."""
        try:
            return self._cfg.get('AzureBatch', 'autoscale')
        except ConfigParser.NoOptionError:
            return None

    def store_autoscale_formula(self, formula):
        """Cache selected VM SKU for later sessions."""
        self._cfg.set('AzureBatch', 'autoscale', formula)
        self._save_config()

    def available_subscriptions(self):
        """Retrieve the currently available subscriptions to populate
        the subscription selection drop down.
        """
        all_subscriptions = self._call(self.subscription_client.subscriptions.list)
        self.subscriptions = []
        for subscription in all_subscriptions:
                self.subscriptions.append(subscription)
        self.count = len(self.subscriptions)
        return self.subscriptions

    def init_after_subscription_selected(self, subscription_id):
        self.batch_mgmt_client = BatchManagementClient(self.mgmtCredentials, str(subscription_id))
        batch_accounts = self._call(self.batch_mgmt_client.batch_account.list)
        accounts = []
        for account in batch_accounts:
            accounts.append(account)
        self.count = len(accounts)
        self._available_batch_accounts = accounts

    def init_after_batch_account_selected(self, batchaccount, subscription_id):
        self.batch_account = batchaccount.name
        self.batch_url = "https://" + batchaccount.account_endpoint
        #if batchaccount.auto_storage == None:
            #throw exception or display message that account needs autoStorage set through the portal first
        storageAccountId = batchaccount.auto_storage.storage_account_id

        parsedStorageAccountId = msrestazuretools.parse_resource_id(storageAccountId)

        self.storage_account = parsedStorageAccountId['name']

        self.storage_mgmt_client = StorageManagementClient(self.mgmtCredentials, str(subscription_id))

        self.storage_key = self._call(self.storage_mgmt_client.storage_accounts.list_keys, parsedStorageAccountId['resource_group'], self.storage_account).keys[0].value
        
        self._storage = storage.BlockBlobService(
            self.storage_account,
            self.storage_key)

        self._client = batch.BatchExtensionsClient(self.batchCredentials, 
            base_url=self.batch_url,
            storage_client=self._storage)

        self._client.config.add_user_agent(self._user_agent)
        self._log = self._configure_logging(self._cfg.get('AzureBatch', 'logging'))

        self._storage.MAX_SINGLE_PUT_SIZE = 2 * 1024 * 1024

    def available_batch_accounts(self):
        """Retrieve the currently available batch accounts to populate
        the account selection drop down.
        """
        return self._available_batch_accounts
