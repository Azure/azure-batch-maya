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


import sys
import os
import logging
import datetime

try:
    import unittest2 as unittest
except ImportError:
    import unittest

try:
    from unittest import mock
except ImportError:
    import mock

from ui_pools import PoolsUI, BatchAppsPoolInfo
from pools import BatchAppsPools
from batchapps import PoolManager, Configuration, Credentials
from batchapps.pool import Pool, PoolSpecifier

class TestBatchAppsPools(unittest.TestCase):

    def setUp(self):
        self.mock_self = mock.create_autospec(BatchAppsPools)
        self.mock_self._log = logging.getLogger("TestPools")

        return super(TestBatchAppsPools, self).setUp()

    @mock.patch("pools.PoolsUI")
    def test_create_batchappspools(self, mock_ui):

        pools = BatchAppsPools("frame", "call")
        mock_ui.assert_called_with(pools, "frame")

    @mock.patch("pools.PoolManager")
    def test_configure(self, mock_mgr):

        session = mock.Mock(credentials="creds", config="conf")
        BatchAppsPools.configure(self.mock_self, session)

        mock_mgr.assert_called_with("creds", "conf")
        self.assertEqual(session, self.mock_self._session)

    def test_get_pools(self):

        mgr = mock.create_autospec(PoolManager)
        mgr.get_pools.return_value = [mock.Mock(id="1234")]
        mgr.__len__.return_value = 1

        def call(func):
            self.assertEqual(func, mgr.get_pools)
            return func()

        self.mock_self.manager = mgr
        self.mock_self._call = call
        self.mock_self.ui = mock.create_autospec(PoolsUI)
        self.mock_self.ui.create_pool_entry.return_value = "pool_entry"

        displayed = BatchAppsPools.get_pools(self.mock_self)
        self.assertEqual(displayed, ["pool_entry"])
        self.assertEqual(len(self.mock_self.pools), 1)

    @mock.patch("pools.maya")
    def test_update_pool(self, mock_maya):

        pool = mock.create_autospec(Pool)
        pool.current_size = "3"
        pool.target_size = "5"
        pool.auto = "False"
        pool.state = "500"
        pool.id = "12345"
        pool.max_tasks = "2"
        pool.allocation_state = "allocating"
        pool.created = "Now"
        self.mock_self.pools = [pool]

        pool_ui = mock.create_autospec(BatchAppsPoolInfo)
        pool_ui.index = 0

        def call(func):
            self.assertTrue(hasattr(func, '__call__'))
            return func()

        self.mock_self._call = call
        self.mock_self.selected_pool = pool_ui
        self.mock_self.ui = mock.create_autospec(PoolsUI)

        BatchAppsPools.update_pool(self.mock_self, 0)
        pool.update.assert_called_with()
        self.assertEqual(self.mock_self.ui.refresh.call_count, 0)

        BatchAppsPools.update_pool(self.mock_self, 1)
        self.assertEqual(self.mock_self.ui.refresh.call_count, 1)

        mock_maya.refresh.side_effect = ValueError("Error")
        BatchAppsPools.update_pool(self.mock_self, 0)
        self.assertEqual(self.mock_self.ui.refresh.call_count, 2)

    def test_pool_selected(self):

        pool_ui = mock.create_autospec(BatchAppsPoolInfo)
        pool_ui.index = 0

        self.mock_self.selected_pool = None

        BatchAppsPools.pool_selected(self.mock_self, None)
        self.assertFalse(self.mock_self.update_pool.call_count)

        BatchAppsPools.pool_selected(self.mock_self, pool_ui)
        self.mock_self.update_pool.assert_called_with(0)

        BatchAppsPools.pool_selected(self.mock_self, pool_ui)
        pool_ui.collapse.assert_called_with()

    def test_auto_pool(self):

        self.mock_self.pools = [mock.Mock(auto=True), mock.Mock(auto=False)]
        self.mock_self.selected_pool = mock.Mock(index=0)
        self.assertTrue(BatchAppsPools.is_auto_pool(self.mock_self))

        self.mock_self.selected_pool = mock.Mock(index=1)
        self.assertFalse(BatchAppsPools.is_auto_pool(self.mock_self))

        self.mock_self.selected_pool = mock.Mock(index=2)
        self.assertFalse(BatchAppsPools.is_auto_pool(self.mock_self))

    def test_get_pool_size(self):

        self.mock_self.pools = [mock.Mock(target_size=5),
                                mock.Mock(target_size="8"),
                                mock.Mock(target_size=None)]

        self.mock_self.selected_pool = mock.Mock(index=0)
        self.assertEqual(BatchAppsPools.get_pool_size(self.mock_self), 5)

        self.mock_self.selected_pool = mock.Mock(index=1)
        self.assertEqual(BatchAppsPools.get_pool_size(self.mock_self), 8)

        self.mock_self.selected_pool = mock.Mock(index=2)
        self.assertEqual(BatchAppsPools.get_pool_size(self.mock_self), 0)

        self.mock_self.selected_pool = mock.Mock(index=3)
        self.assertEqual(BatchAppsPools.get_pool_size(self.mock_self), 0)

    def test_delete_pool(self):

        mock_pool = mock.create_autospec(Pool)
        mock_pool.delete.return_value = None
        self.mock_self.pools = [mock_pool]

        def call(func):
            self.assertTrue(hasattr(func, "__call__"))
            return func()

        self.mock_self._call = call
        self.mock_self.selected_pool = mock.Mock(index=0)
        self.mock_self.ui = mock.create_autospec(PoolsUI)

        BatchAppsPools.delete_pool(self.mock_self)
        self.assertEqual(self.mock_self.ui.refresh.call_count, 1)

        mock_pool.delete.return_value = 1
        BatchAppsPools.delete_pool(self.mock_self)
        self.assertEqual(self.mock_self.ui.refresh.call_count, 2)

        self.mock_self.selected_pool.index = 1
        BatchAppsPools.delete_pool(self.mock_self)
        self.assertEqual(self.mock_self.ui.refresh.call_count, 2)

    def test_create_pool(self):

        def call(func, **kwargs):
            self.assertTrue(hasattr(func, "__call__"))
            self.assertEqual(kwargs.get("target_size"), 5)
            return func(**kwargs)

        self.mock_self._call = call
        self.mock_self.manager = mock.create_autospec(PoolManager)

        BatchAppsPools.create_pool(self.mock_self, 5)
        self.mock_self.manager.create.assert_called_with(target_size=5)

    @mock.patch("pools.maya")
    def test_resize_pool(self, mock_maya):

        def call(func, *args):
            self.assertTrue(hasattr(func, "__call__"))
            self.assertEqual(args[0], 5)
            return func(*args)

        mock_pool = mock.create_autospec(Pool)
        mock_pool.delete.return_value = None
        self.mock_self.pools = [mock_pool]

        self.mock_self._call = call
        self.mock_self.selected_pool = mock.Mock(index=0)
        self.mock_self.ui = mock.create_autospec(PoolsUI)

        BatchAppsPools.resize_pool(self.mock_self, 5)
        self.assertFalse(self.mock_self.ui.refresh.call_count)

        BatchAppsPools.resize_pool(self.mock_self, "5")
        self.assertFalse(self.mock_self.ui.refresh.call_count)

        BatchAppsPools.resize_pool(self.mock_self, None)
        self.assertEqual(self.mock_self.ui.refresh.call_count, 1)


class TestPoolsCombined(unittest.TestCase):

    @mock.patch("ui_pools.utils")
    @mock.patch("ui_pools.maya")
    @mock.patch("pools.maya")
    def test_pools(self, *args):

        def add_tab(tab):
            self.assertFalse(tab.ready)

        def call(func, *args, **kwargs):
            self.assertTrue(hasattr(func, '__call__'))
            return func(*args, **kwargs)

        layout = mock.Mock(add_tab=add_tab)
        pools = BatchAppsPools(layout, call)

        creds = mock.create_autospec(Credentials)
        conf = mock.create_autospec(Configuration)
        session = mock.Mock(credentials=creds, config=conf)

        pools.configure(session)

        pools.manager = mock.create_autospec(PoolManager)

        pool1 = mock.create_autospec(Pool)
        pool1.current_size = "3"
        pool1.target_size = "5"
        pool1.auto = False
        pool1.state = "500"
        pool1.id = "12345"
        pool1.max_tasks = "2"
        pool1.allocation_state = "allocating"
        pool1.created = "now"

        pool2 = mock.create_autospec(Pool)
        pool2.id = "67890"

        pools.manager.get_pools.return_value = []
        pools.manager.__len__.return_value = 0

        pools.ui.prepare()
        self.assertIsNone(pools.selected_pool)
        self.assertEqual(pools.pools, [])
        self.assertTrue(pools.ui.ready)

        pools.manager.get_pools.return_value = [pool1, pool2]
        pools.manager.__len__.return_value = 2

        pools.ui.refresh()
        self.assertIsNone(pools.selected_pool)
        self.assertEqual(pools.pools, [pool1, pool2])
        self.assertEqual(len(pools.ui.pools_displayed), 2)
        self.assertEqual(pools.ui.pools_displayed[0].index, 0)

        pools.ui.pools_displayed[0].on_expand()
        self.assertIsNone(pools.selected_pool)

        pool1.created = str(datetime.datetime.now()).replace(' ', 'T')
        pools.ui.pools_displayed[0].on_expand()
        self.assertEqual(pools.ui.pools_displayed[0], pools.selected_pool)

        pools.ui.pools_displayed[1].on_expand()
        self.assertIsNone(pools.selected_pool)

        pools.ui.pools_displayed[0].on_expand()
        self.assertEqual(pools.get_pool_size(), 5)
        self.assertFalse(pools.is_auto_pool())

        pools.resize_pool(10)
        pool1.resize.assert_called_with(10)
        pool1.resize.side_effect = Exception("failed!")

        pools.resize_pool(8)
        self.assertIsNone(pools.selected_pool)

        pools.ui.pools_displayed[0].on_expand()
        pools.ui.pools_displayed[0].collapse()
        self.assertIsNone(pools.selected_pool)

        pools.ui.pools_displayed[0].on_expand()
        pools.delete_pool()
        pool1.delete.assert_called_with()
        self.assertIsNone(pools.selected_pool)