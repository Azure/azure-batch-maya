# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import ConfigParser
import os
import json
import datetime
import dateutil.tz
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
        self.can_init_from_config = False
        self.ui = ConfigUI(self, settings, frame)
        self._configure_plugin(False)

        #TODO as part of init should check batch and storage clients work somehow 
        #old method with dummy listPool etc calls slowed down opening,
        #so maybe do this in background after UI has been fully loaded

    @property
    def batch(self):
        return self._client

    @property
    def subscription_client(self):
        try:
            return self._subscription_client
        except AttributeError:
            self._subscription_client = None
            return self._subscription_client

    @subscription_client.setter
    def subscription_client(self, value):
        self._subscription_client = value

    @property
    def batch_mgmt_client(self):
        try:
            return self._batch_mgmt_client
        except AttributeError:
            self._batch_mgmt_client = None
            return self._batch_mgmt_client

    @batch_mgmt_client.setter
    def batch_mgmt_client(self, value):
        self._batch_mgmt_client = value

    @property
    def storage(self):
        return self._storage

    @property
    def batch_auth_token(self):
        try:
            return self._batch_auth_token
        except AttributeError:
            self._batch_auth_token = None
            return self._batch_auth_token

    @batch_auth_token.setter
    def batch_auth_token(self, value):
        self._batch_auth_token = value

    @property
    def mgmt_auth_token(self):
        try:
            return self._mgmt_auth_token
        except AttributeError:
            self._mgmt_auth_token = None
            return self._mgmt_auth_token

    @mgmt_auth_token.setter
    def mgmt_auth_token(self, value):
        self._mgmt_auth_token = value

    @property
    def subscription_name(self):
        try:
            return self._subscription_name
        except AttributeError:
            self._subscription_name = None
            return self._subscription_name

    @subscription_name.setter
    def subscription_name(self, value):
        self._subscription_name = value

    @property
    def batch_account(self):
        try:
            return self._batch_account
        except AttributeError:
            self._batch_account = None
            return self._batch_account

    @batch_account.setter
    def batch_account(self, value):
        self._batch_account = value

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
        else:
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
            self._configure_post_auth()

    def _configure_post_auth(self):
        self.mgmtCredentials = AADTokenCredentials(self.mgmt_auth_token)
        self.batchCredentials = AADTokenCredentials(self.batch_auth_token)

        if self.can_init_from_config:
            self.init_from_config()

        else:
            self.subscription_client = SubscriptionClient(self.mgmtCredentials)
            self.ui.init_post_auth() 

    def need_to_refresh_auth_tokens(self, auth_token_list):

        currentTime = datetime.datetime.now()

        tokenRefreshThresholdSeconds = 5 * 60

        for token in auth_token_list:
            if (dateparse(token['expiresOn']) - currentTime).total_seconds() < tokenRefreshThresholdSeconds:
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

        code = context.acquire_user_code(self.mgmtAadResource, self.aadClientId)
        self._log.info(code['message'])
        
        self.ui.prompt_for_login(code['message'])
        maya.refresh()

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
            self.convert_utc_expireson_to_local_timezone_naive(self._batch_auth_token)
        except ConfigParser.NoOptionError:
            self._batch_auth_token = ""
        try:
            self._mgmt_auth_token = json.loads(self._cfg.get('AzureBatch', 'mgmt_auth_token'))
            self.convert_utc_expireson_to_local_timezone_naive(self._mgmt_auth_token)
        except ConfigParser.NoOptionError:
            self._mgmt_auth_token = ""

        #set to true optimistically here, if any values are missing then this must be an old config format
        self.can_init_from_config = True
        try:
            self.subscription_id = self._cfg.get('AzureBatch', 'subscription_id')
        except ConfigParser.NoOptionError:
            self.subscription_id = ""
            self.can_init_from_config = False
        try:
            self._subscription_name = self._cfg.get('AzureBatch', 'subscription_name')
        except ConfigParser.NoOptionError:
            self._subscription_name = ""
            self.can_init_from_config = False
        try:
            self.batch_url = self._cfg.get('AzureBatch', 'batch_url')
        except ConfigParser.NoOptionError:
            self.batch_url = ""
            self.can_init_from_config = False
        try:
            self.batch_account = self._cfg.get('AzureBatch', 'batch_account')
            self.can_init_from_config = True
        except ConfigParser.NoOptionError:
            self.batch_account = ""
            self.can_init_from_config = False
        try:
            self.storage_account_resource_id = self._cfg.get('AzureBatch', 'storage_account_resource_id')
        except ConfigParser.NoOptionError:
            self.storage_account_resource_id = ""
            self.can_init_from_config = False
        try:
            self.storage_key = self._cfg.get('AzureBatch', 'storage_key')
        except ConfigParser.NoOptionError:
            self.storage_key = ""
            self.can_init_from_config = False
        try:
            self.logging_level = self._cfg.getint('AzureBatch', 'logging')
            self._log = self._configure_logging(self.logging_level)
        except ConfigParser.NoOptionError:
            self.logging_level = self.default_logging()
        try:
            self.threads = self._cfg.getint('AzureBatch', 'threads')
        except ConfigParser.NoOptionError:
            self.threads = 20
        finally:
            if self._client != None:
                self._client.threads = self.threads

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
        self._cfg.set('AzureBatch', 'logging', str(level))
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
        self.ensure_azurebatch_config_section_exists()
        self._cfg.set('AzureBatch', 'batch_url', self.batch_url)
        self._cfg.set('AzureBatch', 'batch_account', self.batch_account)
        self._cfg.set('AzureBatch', 'subscription_id', self.subscription_id)
        self._cfg.set('AzureBatch', 'subscription_name', self.subscription_name)
        self._cfg.set('AzureBatch', 'storage_account_resource_id', self.storage_account_resource_id)
        self._cfg.set('AzureBatch', 'storage_key', self.storage_key)
        self._cfg.set('AzureBatch', 'logging', self.logging_level)

        self.convert_timezone_naive_expireson_to_utc(self.mgmt_auth_token)
        self.convert_timezone_naive_expireson_to_utc(self.batch_auth_token)

        self._cfg.set('AzureBatch', 'mgmt_auth_token', json.dumps(self.mgmt_auth_token))
        self._cfg.set('AzureBatch', 'batch_auth_token', json.dumps(self.batch_auth_token))
        self._save_config()

    def ensure_azurebatch_config_section_exists(self):
        try:
            self._cfg.add_section('AzureBatch')
        except ConfigParser.DuplicateSectionError:
            pass
    
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

    def get_cached_subscription(self):
        """Attempt to retrieve a selected subscription from a previous session."""
        try:
            return self._cfg.get('AzureBatch', 'subscription_id')
        except ConfigParser.NoOptionError:
            return None

    def get_cached_batch_account(self):
        """Attempt to retrieve a selected batch account from a previous session."""
        try:
            return self._cfg.get('AzureBatch', 'batch_account')
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
        if not self.subscription_client:
            self.subscription_client = SubscriptionClient(self.mgmtCredentials)
        all_subscriptions = self._call(self.subscription_client.subscriptions.list)
        self.subscriptions = []
        for subscription in all_subscriptions:
            self.subscriptions.append(subscription)
        self.count = len(self.subscriptions)
        return self.subscriptions

    def init_after_subscription_selected(self, subscription_id, subscription_name):
        self.subscription_id = subscription_id
        self.subscription_name = subscription_name
        self.batch_mgmt_client = BatchManagementClient(self.mgmtCredentials, str(subscription_id))
        #batch_accounts = self._call(self.batch_mgmt_client.batch_account.list)
        #accounts = []
        #for account in batch_accounts:
        #    if account.auto_storage != None:
        #        accounts.append(account)
        #self.count = len(accounts)
        #self._available_batch_accounts = accounts

    def init_after_batch_account_selected(self, batchaccount, subscription_id):
        self.batch_account = batchaccount.name
        self.batch_url = "https://" + batchaccount.account_endpoint

        storageAccountId = batchaccount.auto_storage.storage_account_id
        self.storage_account_resource_id = storageAccountId

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
        self.logging_level = self.default_logging()
        self.save_changes()
        self._log = self._configure_logging(self.logging_level)

        self._storage.MAX_SINGLE_PUT_SIZE = 2 * 1024 * 1024

        self._storage.MAX_SINGLE_PUT_SIZE = 2 * 1024 * 1024

    def init_from_config(self):
        parsedStorageAccountId = msrestazuretools.parse_resource_id(self.storage_account_resource_id)
        self.storage_account = parsedStorageAccountId['name']

        self.storage_mgmt_client = StorageManagementClient(self.mgmtCredentials, str(self.subscription_id))

        self.storage_key = self._call(self.storage_mgmt_client.storage_accounts.list_keys, parsedStorageAccountId['resource_group'], self.storage_account).keys[0].value
        
        self._storage = storage.BlockBlobService(
            self.storage_account,
            self.storage_key)

        self._client = batch.BatchExtensionsClient(self.batchCredentials, 
            base_url=self.batch_url,
            storage_client=self._storage)

        self.ui.selected_subscription_id = self.subscription_id

        self._client.config.add_user_agent(self._user_agent)
        self.save_changes()
        self._log = self._configure_logging(self.logging_level)
        self._storage.MAX_SINGLE_PUT_SIZE = 2 * 1024 * 1024

        self.ui.init_from_config()

    def available_batch_accounts(self):
        """Retrieve the currently available batch accounts to populate
        the account selection drop down.
        """
        if not self.batch_mgmt_client:
             self.batch_mgmt_client = BatchManagementClient(self.mgmtCredentials, str(self.subscription_id))
        batch_accounts = self._call(self.batch_mgmt_client.batch_account.list)
        accounts = []
        for account in batch_accounts:
            if account.auto_storage != None:
                accounts.append(account)
        self.count = len(accounts)
        self._available_batch_accounts = accounts

        return self._available_batch_accounts

    def default_logging(self):
        return 10

    def convert_timezone_naive_expireson_to_utc(self, token):
        # we want to store token expiry times as UTC for consistency
        if 'expiresOnUTC' not in token:
            expireson_local = dateparse(token['expiresOn']).replace(tzinfo=dateutil.tz.tzlocal())
            expireson_utc = expireson_local.astimezone(dateutil.tz.gettz('UTC'))
            token['expiresOnUTC'] = str(expireson_utc)
            del token['expiresOn']

    def convert_utc_expireson_to_local_timezone_naive(self, token):
        #the standard token expireson format which the various AAD libraries expect / return is a vanilla datetime string, in local time and timezone naive (no tz specified)
        localtz = dateutil.tz.tzlocal()
        expireson_utc = dateparse(token['expiresOnUTC']).replace(tzinfo = dateutil.tz.gettz('UTC'))
        expireson_local = expireson_utc.astimezone(dateutil.tz.tzlocal())
        expireson_local_tz_naive = expireson_local.replace(tzinfo = None)
        token['expiresOn'] = str(expireson_local_tz_naive)
        del token['expiresOnUTC']