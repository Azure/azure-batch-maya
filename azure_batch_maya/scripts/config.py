#-------------------------------------------------------------------------
#
# Azure Batch Maya Plugin
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

import ConfigParser
import os
import logging
import sys
import traceback

from ui_config import ConfigUI
from api import MayaAPI as maya

import azure.storage.blob as storage
import batch_extensions as batch
from batch_extensions.batch_auth import SharedKeyCredentials


VERSION = os.environ['AZUREBATCH_VERSION']
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
        self._user_agent = "batchmaya/{}".format(VERSION)
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
            self._log = self._configure_logging(10)
            return
        try:
            self._cfg.read(config_file)
            self._storage = storage.BlockBlobService(
                self._cfg.get('AzureBatch', 'storage_account'),
                self._cfg.get('AzureBatch', 'storage_key'))
            self._storage.MAX_SINGLE_PUT_SIZE = 2 * 1024 * 1024
            credentials = SharedKeyCredentials(
                self._cfg.get('AzureBatch', 'batch_account'),
                self._cfg.get('AzureBatch', 'batch_key'))
            self._client = batch.BatchExtensionsClient(
                credentials, base_url=self._cfg.get('AzureBatch', 'batch_url'),
                storage_client=self._storage)
            self._client._config.add_user_agent(self._user_agent)
            self._log = self._configure_logging(
                self._cfg.get('AzureBatch', 'logging'))
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError) as exp:
            # We should only worry about this if it happens when authenticating
            # using the UI, otherwise it's expected.
            if self.ui:
                raise ValueError("Invalid Configuration File: {}".format(exp))

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
            self.ui.logging = int(self._cfg.get('AzureBatch', 'logging'))
        except ConfigParser.NoOptionError:
            self.ui.logging = 10
        self.ui.set_authenticate(self._auth)

    def _auto_authentication(self):
        """Test whether the clients are correctly authenticated
        by doing some quick API calls.
        """
        try:
            filter = batch.models.PoolListOptions(max_results=1, select="id")
            self._client.pool.list(filter)
            self._storage.list_containers(num_results=1)
            return True
        except Exception as exp:
            self._log.info("Failed to authenticate: {0}".format(exp))
            return False

    def set_logging(self, level):
        """Set the logging level to that specified in the UI.
        :param str level: The specified logging level.
        """
        log_level = int(LOG_LEVELS[level])
        self._log.setLevel(log_level)
        self._cfg.set('AzureBatch', 'logging', str(level))

    def save_changes(self):
        """Persist configuration changes to file for future sessions."""
        try:
            self._cfg.add_section('AzureBatch')
        except ConfigParser.DuplicateSectionError:
            pass
        self._cfg.set('AzureBatch', 'batch_url', self.ui.endpoint)
        self._cfg.set('AzureBatch', 'batch_account', self.ui.account)
        self._cfg.set('AzureBatch', 'batch_key', self.ui.key)
        self._cfg.set('AzureBatch', 'storage_account', self.ui.storage)
        self._cfg.set('AzureBatch', 'storage_key', self.ui.storage_key)
        self._cfg.set('AzureBatch', 'logging', self.ui.logging)
        config_file = os.path.join(self._data_dir, self._ini_file)
        with open(config_file, 'w') as handle:
            self._cfg.write(handle)

    def authenticate(self):
        """Begin authentication - initiated by the UI button."""
        try:
            self._configure_plugin()
            self._auth = self._auto_authentication()
        except ValueError as exp:
            maya.error(exp)
            self._auth = False
        finally:
            self.ui.set_authenticate(self._auth)
            self.session()

    def get_cached_vm_sku(self):
        """Attempt to retrieve a selected VM SKU from a previous session."""
        try:
            return self._cfg.get('AzureBatch', 'vm_sku')
        except ConfigParser.NoOptionError:
            return None

    def store_vm_sku(self, sku):
        """Cache selected VM SKU for later sessions."""
        self._cfg.set('AzureBatch', 'vm_sku', sku)
        config_file = os.path.join(self._data_dir, self._ini_file)
        with open(config_file, 'w') as handle:
            self._cfg.write(handle)

    def get_cached_image(self):
        """Attempt to retrieve a selected image a previous session."""
        try:
            return self._cfg.get('AzureBatch', 'image')
        except ConfigParser.NoOptionError:
            return None

    def store_image(self, image):
        """Cache selected image for later sessions."""
        self._cfg.set('AzureBatch', 'image', image)
        config_file = os.path.join(self._data_dir, self._ini_file)
        with open(config_file, 'w') as handle:
            self._cfg.write(handle)

    def get_cached_autoscale_formula(self):
        """Attempt to retrieve an autoscale forumla from a previous session."""
        try:
            return self._cfg.get('AzureBatch', 'autoscale')
        except ConfigParser.NoOptionError:
            return None

    def store_autoscale_formula(self, formula):
        """Cache selected VM SKU for later sessions."""
        self._cfg.set('AzureBatch', 'autoscale', formula)
        config_file = os.path.join(self._data_dir, self._ini_file)
        with open(config_file, 'w') as handle:
            self._cfg.write(handle)
