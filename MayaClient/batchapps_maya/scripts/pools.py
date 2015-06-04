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

import os
import logging

from api import MayaAPI as maya

from ui_pools import PoolsUI

from batchapps import PoolManager
from batchapps.exceptions import RestCallException, FileDownloadException



class BatchAppsPools(object):
    
    def __init__(self, frame, call):

        self._log = logging.getLogger('BatchAppsMaya')
        self._call = call               
        self._session = None

        self.manager = None

        self.ui = PoolsUI(self, frame)
        self.pools = []
        self.selected_pool = None

    def configure(self, session):
        self._session = session
        self.manager = PoolManager(self._session.credentials, self._session.config)

    def list_pools(self, lazy=False):
        #if lazy and self.pools:
        #    return [pool.id for pool in self.pools if not pool.auto]

        self.pools = self._call(self.manager.get_pools)
        self.count = len(self.manager)
        return [pool.id for pool in self.pools if not pool.auto]

    def get_pools(self):
        #if self.ui.ready or not self.pools:
        self.list_pools()

        display_pools = []
        for index, pool in enumerate(self.pools):
            display_pools.append(self.ui.create_pool_entry(pool.id, index))

        return display_pools

    def pool_selected(self, pool_ui):
        if self.selected_pool and pool_ui:
            self.selected_pool.collapse()

        self.selected_pool = pool_ui
        if pool_ui:
            self.update_pool(pool_ui.index)

    def update_pool(self, index):
        try:
            pool = self.pools[index]
            self.selected_pool.set_label("loading...")
            maya.refresh()

            self._call(pool.update)
            self.selected_pool.set_label(pool.id)
            self.selected_pool.set_size(pool.current_size)
            self.selected_pool.set_target(pool.target_size)
            self.selected_pool.set_type("Auto" if pool.auto else "Provisioned")
            self.selected_pool.set_state(pool.state)
            self.selected_pool.set_tasks(pool.max_tasks)
            self.selected_pool.set_allocation(pool.allocation_state)
            self.selected_pool.set_created(pool.created)
            maya.refresh()

        except Exception as exp:
            self._log.warning(str(exp))
            self.ui.refresh()

    def is_auto_pool(self):
        try:
            pool = self.pools[self.selected_pool.index]
            return pool.auto
        except (IndexError, TypeError, AttributeError) as exp:
            self._log.info("Unable to retrieve selected pool {0}".format(exp))
            return False

    def delete_pool(self):
        try:
            pool = self.pools[self.selected_pool.index]
            resp = self._call(pool.delete)

        except (IndexError, TypeError, AttributeError) as exp:
            self._log.info("Unable to retrieve selected pool {0}".format(exp))
            return

        if not resp:
            self._log.info("Pool was unable to be deleted.")
        self.ui.refresh()
    
    def get_pool_size(self):
        try:
            pool = self.pools[self.selected_pool.index]
            return int(pool.target_size)

        except (IndexError, TypeError, AttributeError) as exp:
            self._log.info("Failed to parse pool target size {0}".format(exp))
            return 0

    def create_pool(self, size):
        return self._call(self.manager.create, target_size=int(size))

    def resize_pool(self, new_size):
        self._log.info("Resizing pool...")
        try:
            self.selected_pool.change_resize_label("Resizing...")
            maya.refresh()

            pool = self.pools[self.selected_pool.index]
            self._call(pool.resize, int(new_size))
            self.selected_pool.change_resize_label("Resize Pool")
            self.selected_pool.set_target(new_size)
            maya.refresh()

        except Exception as exp:
            self._log.info("Failed to resize pool {0}".format(exp))
            self.ui.refresh()

