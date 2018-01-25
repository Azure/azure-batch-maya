# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import logging
import os
import sys
import traceback

from ui_shared import AzureBatchUI
from config import AzureBatchConfig
from submission import AzureBatchSubmission
from jobhistory import AzureBatchJobHistory
from assets import AzureBatchAssets
from pools import AzureBatchPools
from environment import AzureBatchEnvironment

from azurebatchmayaapi import MayaAPI as maya
from azure.batch.models import BatchErrorException


ACCEPTED_ERRORS = [
    "JobNotFound",
    "PoolNotFound",
]


class AzureBatchSettings(object):

    tab_index = {
        'AUTH': 1,
        'SUBMIT': 2,
        'ASSETS': 3,
        'POOLS': 4,
        'JOBHISTORY': 5,
        'ENV': 6
    }

    @staticmethod
    def starter():
        """Called by the mel script when the shelf button is clicked."""
        AzureBatchSettings()

    def __init__(self):
        """Initialize all the tabs and attempt to authenticate using cached
        credentials if available.
        """
        self._log = logging.getLogger('AzureBatchMaya')
        try:
            self.frame = AzureBatchUI(self)
            self.config = AzureBatchConfig(self.tab_index['AUTH'], self, self.frame, self.start, self.call)

            if(self.config.can_init_from_config):
                self.init_after_account_selected()

        except Exception as exp:
            if (maya.window("AzureBatch", q=1, exists=1)):
                maya.delete_ui("AzureBatch")
            message = "Batch Plugin Failed to Start: {0}".format(exp)
            maya.error(message)
            raise

    def init_after_account_selected(self):
        try:
            if not hasattr(self, "submission"):
                self.submission = AzureBatchSubmission(self.tab_index['SUBMIT'], self.frame, self.call)
            if not hasattr(self, "assets"):
                self.assets = AzureBatchAssets(self.tab_index['ASSETS'], self.frame, self.call)
            if not hasattr(self, "pools"):
                self.pools = AzureBatchPools(self.tab_index['POOLS'], self.frame, self.call)
            if not hasattr(self, "jobhistory"):
                self.jobhistory =  AzureBatchJobHistory(self.tab_index['JOBHISTORY'], self.frame, self.call)
            if not hasattr(self, "env"):
                self.env =  AzureBatchEnvironment(self.tab_index['ENV'], self.frame, self.call)
            self.start()
        except Exception as exp:
            if (maya.window("AzureBatch", q=1, exists=1)):
                maya.delete_ui("AzureBatch")
            message = "Batch Plugin Failed to Start: {0}".format(exp)
            maya.error(message)
            raise

    def start(self):
        """Start the plugin UI. Depending on whether auto-authentication was
        successful, the plugin will start by displaying the submission tab.
        Otherwise the UI will be disabled, and the login tab will be displayed.
        """
        try:
            self._log.debug("Starting AzureBatchShared...")
            self.frame.is_logged_in()
            self.env.configure(self.config)
            self.jobhistory.configure(self.config)
            self.assets.configure(self.config)
            self.pools.configure(self.config, self.env)
            self.submission.start(self.config, self.assets, self.pools, self.env)
        except Exception as exp:
            self._log.warning(exp)
            if (maya.window("AzureBatch", q=1, exists=1)):
                maya.delete_ui("AzureBatch")
            maya.error("Batch Plugin UI failed to load:\n{0}".format(exp))

    def call(self, command, *args, **kwargs):
        """Wrap all Batch and Storage API calls in order to handle errors.
        Some errors we anticipate and raise without a dialog (e.g. PoolNotFound).
        Others we raise and display to the user.
        """
        try:
            return command(*args, **kwargs)
        except BatchErrorException as exp:
            if exp.error.code in ACCEPTED_ERRORS:
                self._log.info("Call failed: {}".format(exp.error.code))
                raise
            else:
                message = exp.error.message.value
                if exp.error.values:
                    message += "Details:\n"
                    for detail in exp.error.values:
                        message += "{}: {}".format(detail.key, detail.value)
                raise ValueError(message)
        except Exception as exp:
            if (maya.window("AzureBatch", q=1, exists=1)):
                maya.delete_ui("AzureBatch")
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self._log.error("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
            raise ValueError("Error: {0}".format(exp))
