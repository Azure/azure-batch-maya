#-------------------------------------------------------------------------
#
# Batch Apps Maya Plugin
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

import logging
import webbrowser
import os
import threading

from ui_shared import BatchAppsUI

from config import BatchAppsConfig
from submission import BatchAppsSubmission
from history import BatchAppsHistory
from assets import BatchAppsAssets
from pools import BatchAppsPools
from environment import BatchAppsEnvironment

from api import MayaAPI as maya

from batchapps.exceptions import (
    InvalidConfigException,
    RestCallException,
    SessionExpiredException,
    FileDownloadException)

class BatchAppsSettings(object):

    @staticmethod
    def starter():
        BatchAppsSettings()

    def __init__(self):

        self._log = logging.getLogger('BatchAppsMaya')
        
        try:
            self.frame = BatchAppsUI(self)

            self.config = BatchAppsConfig(self.frame, self.start)
            self.submission = BatchAppsSubmission(self.frame, self.call)
            self.assets = BatchAppsAssets(self.frame, self.call)
            self.pools = BatchAppsPools(self.frame, self.call)
            self.env = BatchAppsEnvironment(self.frame, self.call)
            self.history =  BatchAppsHistory(self.frame, self.call)

            self.start()

        except Exception as exp:
            if (maya.window("BatchApps", q=1, exists=1)):
                maya.delete_ui("BatchApps")

            message = "Batch Plugin Failed to Start: {0}".format(exp)
            maya.error(message)

    def start(self):
        try:
            self._log.debug("Starting BatchAppsShared...")

            if self.config.auth:
                self.frame.is_logged_in()

                self.history.configure(self.config)
                self.assets.configure(self.config)
                self.pools.configure(self.config)
                self.env.configure(self.config)

                self.submission.start(self.config, self.assets, self.pools, self.env)

            else:
                self.frame.is_logged_out()

        except Exception as exp:
            if (maya.window("BatchApps", q=1, exists=1)):
                maya.delete_ui("BatchApps")

            maya.error("Batch Plugin UI failed to load:\n{0}".format(exp))

    def call(self, command, *args, **kwargs):
        try:
            return command(*args, **kwargs)

        except SessionExpiredException as exp:
            self.frame.is_logged_out()   
            raise  

        except RestCallException as exp:
            maya.error("API call failed: {0}".format(exp))
            raise

        except FileDownloadException as exp:
            raise

        except Exception as exp:
            if (maya.window("BatchApps", q=1, exists=1)):
                maya.delete_ui("BatchApps")
            maya.error("Error: {0}".format(exp))
            raise

