# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import ConfigParser
import os
import logging
import sys
import traceback

from ui_config import ConfigUI
from azurebatchmayaapi import MayaAPI as maya

import azure.storage.blob as storage
import azure.batch_extensions as batch
from azure.batch.batch_auth import SharedKeyCredentials


LOG_LEVELS = {
    'debug':10,
    'info':20,
    'warning':30,
    'error':40}


class AzureBatchConfig(object):
    """Handler for authentication and configuration of the SDK clients."""

    def __init__(self, index, frame, start):
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
        self._configure_plugin()
        self.ui = ConfigUI(self, frame)
        self._auth = self._auto_authentication()
        self._update_config_ui()

    @property
    def batch(self):
        return self._client

    @property
    def storage(self):
        return self._storage

    @property
    def auth(self):
        return self._auth

    @property
    def path(self):
        return os.path.join(self._data_dir, self._ini_file)

    def _configure_plugin(self):
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
            self._storage = storage.BlockBlobService(
                self._cfg.get('AzureBatch', 'storage_account'),
                self._cfg.get('AzureBatch', 'storage_key'),
                endpoint_suffix = self._cfg.get('AzureBatch', 'storage_suffix'))
            self._storage.MAX_SINGLE_PUT_SIZE = 2 * 1024 * 1024
            credentials = SharedKeyCredentials(
                self._cfg.get('AzureBatch', 'batch_account'),
                self._cfg.get('AzureBatch', 'batch_key'))
            self._client = batch.BatchExtensionsClient(
                credentials, base_url=self._cfg.get('AzureBatch', 'batch_url'),
                storage_client=self._storage)
            self._client.config.add_user_agent(self._user_agent)
            self._log = self._configure_logging(
                self._cfg.get('AzureBatch', 'logging'))
        except Exception as exp:
            # We should only worry about this if it happens when authenticating
            # using the UI, otherwise it's expected.
            if self.ui:
                raise ValueError("Invalid Configuration: {}".format(exp))
            else:
                # We'll need a place holder logger
                self._log = self._configure_logging(LOG_LEVELS['debug'])

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

    def _update_config_ui(self):
        """Populate the config tab UI with the values loaded from the
        configuration file.
        """
        try:
            self._cfg.add_section('AzureBatch')
        except ConfigParser.DuplicateSectionError:
            pass
        try:
            self.ui.endpoint = self._cfg.get('AzureBatch', 'batch_url')
        except ConfigParser.NoOptionError:
            self.ui.endpoint = ""
        try:
            self.ui.account = self._cfg.get('AzureBatch', 'batch_account')
        except ConfigParser.NoOptionError:
            self.ui.account = ""
        try:
            self.ui.key = self._cfg.get('AzureBatch', 'batch_key')
        except ConfigParser.NoOptionError:
            self.ui.key = ""
        try:
            self.ui.storage = self._cfg.get('AzureBatch', 'storage_account')
        except ConfigParser.NoOptionError:
            self.ui.storage = ""
        try:
            self.ui.storage_key = self._cfg.get('AzureBatch', 'storage_key')
        except ConfigParser.NoOptionError:
            self.ui.storage_key = ""
        try:
            self.ui.storage_suffix = self._cfg.get('AzureBatch', 'storage_suffix')
        except ConfigParser.NoOptionError:
            self.ui.storage_suffix = "core.windows.net"
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
        self._cfg.set('AzureBatch', 'batch_url', self.ui.endpoint)
        self._cfg.set('AzureBatch', 'batch_account', self.ui.account)
        self._cfg.set('AzureBatch', 'batch_key', self.ui.key)
        self._cfg.set('AzureBatch', 'storage_account', self.ui.storage)
        self._cfg.set('AzureBatch', 'storage_key', self.ui.storage_key)
        self._cfg.set('AzureBatch', 'storage_suffix', self.ui.storage_suffix)
        self._save_config()

    def authenticate(self):
        """Begin authentication - initiated by the UI button."""
        try:
            self._configure_plugin()
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
