﻿# --------------------------------------------------------------------------------------------
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
import copy

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

from adal import AdalError

from aadEnvironmentProvider import AADEnvironmentProvider

LOG_LEVELS = {
    'debug':10,
    'info':20,
    'warning':30,
    'error':40}


class AzureBatchConfig(object):
    """Handler for authentication and configuration of the SDK clients."""

    aadClientId = "04b07795-8ddb-461a-bbee-02f9e1bf7b46" #Azure CLI

    def __init__(self):
        self._data_dir = os.path.join(maya.prefs_dir(), 'AzureBatchData')
        if not os.path.isdir(self._data_dir):
            try:
                os.makedirs(self._data_dir)
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        self._log = self._configure_logging(LOG_LEVELS['debug'])    #config hasn't been loaded yet so use a default logging level

    def initialize_ui(self, index, settings, frame, start, call):
        """Create new configuration Handler.

        :param index: The UI tab index.
        :param frame: The shared plug-in UI frame.
        :type frame: :class:`.AzureBatchUI`
        :param func call: The shared REST API call wrapper.
        """
        self.session = start
        self._tab_index = index
       
        self._ini_file = "azure_batch.ini"
        self._user_agent = "batchmaya/{}".format(os.environ.get('AZUREBATCH_VERSION'))
        self._cfg = ConfigParser.ConfigParser()
        self._call = call
        self.aad_environment_provider = AADEnvironmentProvider()
        
        self.ui = ConfigUI(self, settings, frame)
        self._configure_plugin(False)
        self.aad_environment = None

        #TODO as part of init should check batch and storage clients work somehow 
        #old method with dummy listPool etc calls slowed down opening,
        #so maybe do this in background after UI has been fully loaded

    def __getattr__(self, attr):
        #return None rather than throw AttributeError so we don't have to init everything
        return self.__dict__.get(attr, None)

    #property helpers
    def _get_cached_config_value(self, identifier):
        try:
            return self._cfg.get('AzureBatch', identifier)
        except ConfigParser.NoOptionError:
            return None

    def _store_config_value(self, identifier, value):
        self._cfg.set('AzureBatch', identifier, str(value))
        self._save_config()

    #properties from config file
    @property
    def mgmt_auth_token(self):
        value_from_config = self._get_cached_config_value('mgmt_auth_token')
        if value_from_config is None:
            return None
        json_loaded_value = json.loads(value_from_config)
        return self.convert_utc_expireson_to_local_timezone_naive(json_loaded_value)
    @mgmt_auth_token.setter
    def mgmt_auth_token(self, value):
        self._store_config_value('mgmt_auth_token',  json.dumps(self.convert_timezone_naive_expireson_to_utc(value)))

    @property
    def batch_auth_token(self): 
        value_from_config = self._get_cached_config_value('batch_auth_token')
        if value_from_config is None:
            return None
        json_loaded_value = json.loads(value_from_config)
        return self.convert_utc_expireson_to_local_timezone_naive(json_loaded_value)
    @batch_auth_token.setter
    def batch_auth_token(self, value):
        self._store_config_value('batch_auth_token',  json.dumps(self.convert_timezone_naive_expireson_to_utc(value)))

    @property
    def subscription_id(self):
        return self._get_cached_config_value('subscription_id')
    @subscription_id.setter
    def subscription_id(self, value):
        self._store_config_value('subscription_id', value)

    @property
    def subscription_name(self):
        return self._get_cached_config_value('subscription_name')
    @subscription_name.setter
    def subscription_name(self, value):
        self._store_config_value('subscription_name', value)

    @property
    def vm_sku(self):
        value_in_config = self._get_cached_config_value('vm_sku')
        if value_in_config is None:
            return self.default_vm_sku()
        return value_in_config
    @vm_sku.setter
    def vm_sku(self, value):
        self._store_config_value('vm_sku', value)

    @property
    def batch_account(self):
        return self._get_cached_config_value('batch_account')
    @batch_account.setter
    def batch_account(self, value):
        self._store_config_value('batch_account', value)

    @property
    def batch_url(self):
        return self._get_cached_config_value('batch_url')
    @batch_url.setter
    def batch_url(self, value):
        self._store_config_value('batch_url', value)

    @property
    def storage_account_resource_id(self):
        return self._get_cached_config_value('storage_account_resource_id')
    @storage_account_resource_id.setter
    def storage_account_resource_id(self, value):
        self._store_config_value('storage_account_resource_id', value)

    @property
    def custom_image_resource_id(self):
        return self._get_cached_config_value('custom_image_resource_id')
    @custom_image_resource_id.setter
    def custom_image_resource_id(self, value):
        self._store_config_value('custom_image_resource_id', value)

    @property
    def container_image(self):
        return self._get_cached_config_value('container_image')
    @container_image.setter
    def container_image(self, value):
        self._store_config_value('container_image', value)

    @property
    def node_sku_id(self):
        return self._get_cached_config_value('node_sku_id')
    @node_sku_id.setter
    def node_sku_id(self, value):
        self._store_config_value('node_sku_id', value)

    @property
    def batch_image(self):
        return self._get_cached_config_value('batch_image')
    @batch_image.setter
    def batch_image(self, value):
        self._store_config_value('batch_image', value)

    @property
    def aad_tenant_name(self):
        return self._get_cached_config_value('aad_tenant_name')
    @aad_tenant_name.setter
    def aad_tenant_name(self, value):
        self._store_config_value('aad_tenant_name', value)

    @property
    def aad_environment_id(self):
        value = self._get_cached_config_value('aad_environment_id')
        return value
    @aad_environment_id.setter
    def aad_environment_id(self, value):
        self._store_config_value('aad_environment_id', value)

    #properties from config file with additional behaviour
    @property
    def logging_level(self):
        value_in_config = self._get_cached_config_value('logging')
        if value_in_config is None:
            return self.default_logging()
        return value_in_config
    @logging_level.setter
    def logging_level(self, value):
        self._log.setLevel(level)
        self._store_config_value('logging', value)

    @property
    def threads(self):
        value_in_config = self._get_cached_config_value('threads')
        if value_in_config is None:
            return self.default_threads()
        return int(value_in_config)
    @threads.setter
    def threads(self, value):
        if self._client != None:
            self._client.threads = self.threads
        self._store_config_value('threads', value)

    #non config file properties
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
    def path(self):
        return os.path.join(self._data_dir, self._ini_file)

    @property
    def auth(self):
        return self._auth
    @auth.setter
    def auth(self, value):
        self._auth = value

    def _configure_plugin(self, from_auth_button):
        """Set up the config file, authenticate the SDK clients
        and set up the log file.
        """
        config_file = os.path.join(self._data_dir, self._ini_file)

        try:
            self._cfg.read(config_file)

            self.ui.disable(True)

            self._read_config_file()

        except Exception as exp:
            # We should only worry about this if it happens when authenticating
            # using the UI, otherwise it's expected.
            if from_auth_button:
                raise ValueError("Invalid Configuration: {}".format(exp))

        self.ui.init_post_config_file_read()

        if(not self.batch_auth_token or not self.mgmt_auth_token):
            self.ui.prompt_for_aad_tenant()
            if self.aad_tenant_name and self.aad_tenant_name != None and self.aad_tenant_name != 'None':
                maya.text_field(self.ui._aad_tenant_field, edit=True, text=self.aad_tenant_name)
                self.ui.aad_tenant_name_changed(self.aad_tenant_name)
                maya.refresh()
        else:
            if self.need_to_refresh_auth_tokens([self.batch_auth_token, self.mgmt_auth_token]):
                refreshedTokens = self.refresh_auth_tokens(self.batch_auth_token, self.mgmt_auth_token)
                if not refreshedTokens:
                    self.prompt_for_and_obtain_aad_tokens()
                    return
            self._configure_post_auth()

    def _configure_post_auth(self):
        self.mgmtCredentials = AADTokenCredentials(self.mgmt_auth_token, 
            cloud_environment=self.aad_environment_provider.getEnvironmentForId(self.aad_environment_id),
            tenant=self.aad_tenant_name)
        self.batchCredentials = AADTokenCredentials(self.batch_auth_token, 
            cloud_environment=self.aad_environment_provider.getEnvironmentForId(self.aad_environment_id),
            tenant=self.aad_tenant_name)

        if self.can_init_from_config:
            self.init_from_config()
            self.ui.init_from_config()

        else:
            self.subscription_client = SubscriptionClient(self.mgmtCredentials, 
                base_url=self.aad_environment_provider.getResourceManager(self.aad_environment_id))
            self.ui.init_post_auth() 

    def update_batch_and_storage_client_creds(self, batch_auth_token, mgmt_auth_token):

        self.batchCredentials = AADTokenCredentials(batch_auth_token,
            cloud_environment=self.aad_environment_provider.getEnvironmentForId(self.aad_environment_id),
            tenant=self.aad_tenant_name)
        self.mgmtCredentials = AADTokenCredentials(mgmt_auth_token,
            cloud_environment=self.aad_environment_provider.getEnvironmentForId(self.aad_environment_id),
            tenant=self.aad_tenant_name)
        self._client._mgmt_credentials = self.mgmtCredentials
        self._client._client.creds = self.batchCredentials
        
        self.storage_mgmt_client._client.creds = self.mgmtCredentials

    def need_to_refresh_auth_tokens(self, auth_token_list):

        currentTime = datetime.datetime.now()

        tokenRefreshThresholdSeconds = 5 * 60

        for token in auth_token_list:
            if (dateparse(token['expiresOn']) - currentTime).total_seconds() < tokenRefreshThresholdSeconds:
                return True
        return False

    def refresh_auth_tokens(self, batch_token, mgmt_token):

        context = adal.AuthenticationContext(self.aad_environment_provider.getAadAuthorityHostUrl(self.aad_environment_id) + '/' + self.aad_tenant_name, api_version=None)

        try:
            self.mgmt_auth_token = context.acquire_token_with_refresh_token(
                mgmt_token['refreshToken'],
                self.aadClientId,
                self.aad_environment_provider.getAadManagementUrl(self.aad_environment_id))

            self.batch_auth_token =  context.acquire_token_with_refresh_token(
                batch_token['refreshToken'],
                self.aadClientId,
                self.aad_environment_provider.getBatchResourceUrl(self.aad_environment_id))

            return True

        except AdalError as exp:
            errors = exp.error_response['error_codes']
            if 70002 in errors or 70008 or 700082 in errors:
                #70002 is: Error validating credentials. 70008 or more recently 700082 is: The refresh token has expired due to inactivity.
                return False
            raise exp

    def prompt_for_and_obtain_aad_tokens(self):
        self.obtain_aad_tokens()
        self.ui.auth_status = "Please follow instructions below to sign in."
        maya.refresh()
        
    def obtain_aad_tokens(self):
        ui_environment_id = self.ui.aad_environment_dropdown.value()
        ui_tenant_name = self.ui.aadTenant
        context = adal.AuthenticationContext(self.aad_environment_provider.getAadAuthorityHostUrl(ui_environment_id) + '/' + ui_tenant_name, api_version=None)

        code = context.acquire_user_code(self.aad_environment_provider.getAadManagementUrl(ui_environment_id), self.aadClientId)
        self._log.info(code['message'])
        
        self.ui.prompt_for_login(code['message'])

        def aad_auth_thread_func(context, code):
            self.mgmt_auth_token = context.acquire_token_with_device_code(self.aad_environment_provider.getAadManagementUrl(ui_environment_id), code, self.aadClientId)
            self.batch_auth_token = context.acquire_token(self.aad_environment_provider.getBatchResourceUrl(ui_environment_id), self.mgmt_auth_token['userId'], self.aadClientId)
            self.aad_environment_id = ui_environment_id
            self.aad_tenant_name = ui_tenant_name
            self.remove_old_batch_account_from_config()
            maya.execute_in_main_thread(self._configure_post_auth)

        authThread = threading.Thread(
            target=aad_auth_thread_func,
            args=(context, code))

        authThread.start()

    def remove_old_batch_account_from_config(self):
        self._cfg.remove_option('AzureBatch', 'batch_url')
        self._cfg.remove_option('AzureBatch', 'batch_account')
        self._cfg.remove_option('AzureBatch', 'subscription_id')
        self._cfg.remove_option('AzureBatch', 'subscription_name')
        self._cfg.remove_option('AzureBatch', 'storage_account_resource_id')
        self._save_config()

    def _configure_logging(self, log_level):
        """Configure the logger. Setup the file output and format
        the log messages.

        :param log_level: The specified level of logging verbosity.
        """
        level = int(log_level)
        logger = logging.getLogger('AzureBatchMaya')
        if len(logger.handlers) == 0:
            file_format = logging.Formatter(
                "%(asctime)-15s [%(levelname)s] %(module)s: %(message)s")
            logfile = os.path.normpath(os.path.join(self._data_dir, "azure_batch.log"))
            if not os.path.exists(logfile):
                with open(logfile, 'w') as handle:
                    handle.write("Azure Batch Plugin Log\n")
            file_logging = logging.FileHandler(logfile)
            file_logging.setFormatter(file_format)
            logger.addHandler(file_logging)
        logger.setLevel(level)
        return logger

    def _read_config_file(self):
        """Populate the config tab UI with the values loaded from the
        configuration file.
        """
        self.ensure_azurebatch_config_section_exists()

        #set to true optimistically here, if any values are missing then this must be an old config format
        self.can_init_from_config = True

        required_config_values = [self.subscription_id, 
                                    self.aad_tenant_name, 
                                    self.subscription_name, 
                                    self.aad_environment_id,
                                    self.batch_url, 
                                    self.batch_account, 
                                    self.storage_account_resource_id, 
                                    self.mgmt_auth_token,
                                    self.batch_auth_token]

        #if a required value is not present in the config, the relevant property will return 'None'
        if None in required_config_values:
            self.can_init_from_config = False

        self._log = self._configure_logging(self.logging_level)

        if self._client != None:
            self._client.threads = self.threads

    def _save_config(self):
        """Persist the current plugin configuration to file."""
        config_file = os.path.join(self._data_dir, self._ini_file)
        with open(config_file, 'w') as handle:
            self._cfg.write(handle)

    def save_changes(self):
        """Persist auth config changes to file for future sessions."""
        self.ensure_azurebatch_config_section_exists()
        #TODO is this method necessary anymore?
        self._cfg.set('AzureBatch', 'batch_url', self.batch_url)
        self._cfg.set('AzureBatch', 'batch_account', self.batch_account)
        self._cfg.set('AzureBatch', 'subscription_id', self.subscription_id)
        self._cfg.set('AzureBatch', 'subscription_name', self.subscription_name)
        self._cfg.set('AzureBatch', 'storage_account_resource_id', self.storage_account_resource_id)
        self._cfg.set('AzureBatch', 'logging', str(self.logging_level))
        self._cfg.set('AzureBatch', 'aad_tenant_name', self.aad_tenant_name)
        self._cfg.set('AzureBatch', 'aad_environment_id', self.aad_environment_id)
        self._save_config()

    def ensure_azurebatch_config_section_exists(self):
        try:
            self._cfg.add_section('AzureBatch')
        except ConfigParser.DuplicateSectionError:
            pass

    def available_subscriptions(self):
        """Retrieve the currently available subscriptions to populate
        the subscription selection drop down.
        """
        if not self.subscription_client:
            self.subscription_client = SubscriptionClient(self.mgmtCredentials,
                 base_url=self.aad_environment_provider.getResourceManager(self.aad_environment_id))
        all_subscriptions = self._call(self.subscription_client.subscriptions.list)
        self.subscriptions = []
        for subscription in all_subscriptions:
            self.subscriptions.append(subscription)
        self.count = len(self.subscriptions)
        return self.subscriptions

    def init_after_subscription_selected(self, subscription_id, subscription_name):
        self.subscription_id = subscription_id
        self.subscription_name = subscription_name
        self.batch_mgmt_client = BatchManagementClient(self.mgmtCredentials, str(subscription_id), 
             base_url=self.aad_environment_provider.getResourceManager(self.aad_environment_id))

    def init_after_batch_account_selected(self, batchaccount, subscription_id):
        self.batch_account = batchaccount.name
        self.batch_url = "https://" + batchaccount.account_endpoint

        storageAccountId = batchaccount.auto_storage.storage_account_id
        self.storage_account_resource_id = storageAccountId

        parsedStorageAccountId = msrestazuretools.parse_resource_id(storageAccountId)
        self.storage_account = parsedStorageAccountId['name']

        self.storage_mgmt_client = StorageManagementClient(self.mgmtCredentials, str(subscription_id),
            base_url=self.aad_environment_provider.getResourceManager(self.aad_environment_id))
        
        try:
            self.storage_key = self._call(self.storage_mgmt_client.storage_accounts.list_keys, parsedStorageAccountId['resource_group'], self.storage_account).keys[0].value
        except Exception as exp:
            self.remove_old_batch_account_from_config()
            raise exp

        self._storage = storage.BlockBlobService(
            self.storage_account,
            self.storage_key)
        self._storage.MAX_SINGLE_PUT_SIZE = 2 * 1024 * 1024

        #TODO refactor move the below shared block into def configureClient(client)
        self._client = batch.BatchExtensionsClient(self.batchCredentials, 
            base_url=self.batch_url,
            storage_client=self._storage)

        self._client.config.add_user_agent(self._user_agent)
        self._client.threads = self.threads
        self._log = self._configure_logging(self.logging_level)


    def init_from_config(self):
        parsedStorageAccountId = msrestazuretools.parse_resource_id(self.storage_account_resource_id)
        self.storage_account = parsedStorageAccountId['name']

        self.storage_mgmt_client = StorageManagementClient(self.mgmtCredentials, str(self.subscription_id),
            base_url=self.aad_environment_provider.getResourceManager(self.aad_environment_id))

        self.storage_key = self._call(self.storage_mgmt_client.storage_accounts.list_keys, parsedStorageAccountId['resource_group'], self.storage_account).keys[0].value
        
        self._storage = storage.BlockBlobService(
            self.storage_account,
            self.storage_key)
        self._storage.MAX_SINGLE_PUT_SIZE = 2 * 1024 * 1024

        #TODO refactor move the below shared block into def configureClient(client)
        self._client = batch.BatchExtensionsClient(self.batchCredentials, 
            base_url=self.batch_url,
            storage_client=self._storage)

        self._client.config.add_user_agent(self._user_agent)
        self._client.threads = self.threads
        self.save_changes()
        self._log = self._configure_logging(self.logging_level)

    def available_batch_accounts(self):
        """Retrieve the currently available batch accounts to populate
        the account selection drop down.
        """
        if not self.batch_mgmt_client:
             self.batch_mgmt_client = BatchManagementClient(self.mgmtCredentials, str(self.subscription_id),
                base_url=self.aad_environment_provider.getResourceManager(self.aad_environment_id))
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

    def default_threads(self):
        return 20

    def default_vm_sku(self):
        return "STANDARD_D3_V2"

    def convert_timezone_naive_expireson_to_utc(self, token):
        # we want to store token expiry times as UTC for consistency
        if token and token is not None and 'expiresOn' in token:
            token_copy = copy.deepcopy(token)
            expireson_local = dateparse(token_copy['expiresOn']).replace(tzinfo=dateutil.tz.tzlocal())
            expireson_utc = expireson_local.astimezone(dateutil.tz.gettz('UTC'))
            token_copy['expiresOnUTC'] = str(expireson_utc)
            del token_copy['expiresOn']
            return token_copy
        else:
            return token

    def convert_utc_expireson_to_local_timezone_naive(self, token):
        #the standard token expireson format which the various AAD libraries expect / return is a vanilla datetime string, in local time and timezone naive (no tz specified)
        if token and token is not None and 'expiresOnUTC' in token:
            token_copy = copy.deepcopy(token)
            localtz = dateutil.tz.tzlocal()
            expireson_utc = dateparse(token_copy['expiresOnUTC']).replace(tzinfo = dateutil.tz.gettz('UTC'))
            expireson_local = expireson_utc.astimezone(dateutil.tz.tzlocal())
            expireson_local_tz_naive = expireson_local.replace(tzinfo = None)
            token_copy['expiresOn'] = str(expireson_local_tz_naive)
            del token_copy['expiresOnUTC']
            return token_copy
        else:
            return token