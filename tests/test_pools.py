# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

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

from ui_pools import PoolsUI, AzureBatchPoolInfo
from pools import AzureBatchPools
from environment import AzureBatchEnvironment
import batch_extensions as batch
from batch_extensions import models


class AzureTestBatchPools(unittest.TestCase):

    def setUp(self):
        self.mock_self = mock.create_autospec(AzureBatchPools)
        self.mock_self._log = logging.getLogger("TestPools")
        self.mock_self.batch = mock.create_autospec(batch.BatchExtensionsClient)
        self.mock_self.batch.pool = mock.create_autospec(batch.operations.ExtendedPoolOperations)
        self.mock_self.environment = mock.create_autospec(AzureBatchEnvironment)
        return super(AzureTestBatchPools, self).setUp()

    @mock.patch("pools.PoolsUI")
    def test_pools_initialize(self, mock_ui):
        pools = AzureBatchPools(4, "frame", "call")
        mock_ui.assert_called_with(pools, "frame")

    def test_pools_configure(self):
        session = mock.Mock(batch="batch")
        AzureBatchPools.configure(self.mock_self, session, "env_manager")
        self.assertEqual("batch", self.mock_self.batch)

    def test_pools_list_pools(self):
        self.mock_self.batch = mock.create_autospec(batch.BatchExtensionsClient)
        self.mock_self.batch.pool = mock.create_autospec(batch.operations.ExtendedPoolOperations)
        pool1 = mock.create_autospec(models.CloudPool)
        pool1.id = "12345"
        pool1.creation_time = datetime.datetime.now()
        pool2 = mock.create_autospec(models.CloudPool)
        pool2.id = "67890"
        pool2.creation_time = datetime.datetime.now()
        self.mock_self._call = lambda x: [pool1, pool2]

        ids = AzureBatchPools.list_pools(self.mock_self)
        self.assertEqual(ids, [])
        self.assertEqual(len(self.mock_self.pools), 0)

        pool1.id = "Maya_Pool_A"
        pool2.id = "Maya_Auto_Pool_B"
        ids = AzureBatchPools.list_pools(self.mock_self)
        self.assertEqual(ids, ["Maya_Pool_A"])
        self.assertEqual(len(self.mock_self.pools), 2)

    def test_pools_get_pools(self):
        def list_pools():
            self.mock_self.pools = [mock.Mock(id="1234", display_name="name")]
        self.mock_self.list_pools = list_pools
        self.mock_self.ui = mock.create_autospec(PoolsUI)
        self.mock_self.ui.create_pool_entry.return_value = "pool_entry"

        displayed = AzureBatchPools.get_pools(self.mock_self)
        self.assertEqual(displayed, ["pool_entry"])
        self.assertEqual(len(self.mock_self.pools), 1)
        self.mock_self.ui.create_pool_entry.assert_called_with('name', 0)

    def test_pools_pool_selected(self):
        pool_ui = mock.create_autospec(AzureBatchPoolInfo)
        pool_ui.index = 0
        self.mock_self.selected_pool = None

        AzureBatchPools.pool_selected(self.mock_self, None)
        self.assertFalse(self.mock_self.update_pool.call_count)
        AzureBatchPools.pool_selected(self.mock_self, pool_ui)
        self.mock_self.update_pool.assert_called_with(0)
        AzureBatchPools.pool_selected(self.mock_self, pool_ui)
        pool_ui.collapse.assert_called_with()


    @mock.patch("pools.maya")
    def test_pools_update_pool(self, mock_maya):
        self.mock_self.batch = mock.create_autospec(batch.BatchExtensionsClient)
        self.mock_self.batch.pool = mock.Mock(get="get")
        self.mock_self.batch.compute_node = mock.Mock(list="list")
        pool = mock.create_autospec(models.CloudPool)
        pool.application_licenses = ["maya", "arnold"]
        pool.display_name = "name"
        pool.current_dedicated_nodes = 3
        pool.target_dedicated_nodes = 5
        pool.state = mock.Mock(value="resizing")
        pool.id = "Maya_Pool_12345"
        pool.max_tasks_per_node = 1
        pool.allocation_state = mock.Mock(value="allocating")
        pool.creation_time = datetime.datetime.now()
        pool.vm_size = "Standard_A1"
        pool.virtual_machine_configuration = mock.create_autospec(batch.models.VirtualMachineConfiguration)
        pool.virtual_machine_configuration.image_reference = "image"
        self.mock_self.environment.get_image_label.return_value = "Batch Windows Image"
        self.mock_self.pools = [pool]
        pool_ui = mock.create_autospec(AzureBatchPoolInfo)
        pool_ui.index = 0

        def call(func, pool_id):
            self.assertEqual(pool_id, 'Maya_Pool_12345')
            if func == "get":
                return pool
            else:
                return []
        self.mock_self._call = call
        self.mock_self.selected_pool = pool_ui
        self.mock_self.ui = mock.create_autospec(PoolsUI)

        AzureBatchPools.update_pool(self.mock_self, 0)
        self.assertEqual(self.mock_self.ui.refresh.call_count, 0)
        self.assertEqual(mock_maya.refresh.call_count, 2)
        AzureBatchPools.update_pool(self.mock_self, 1)
        self.assertEqual(self.mock_self.ui.refresh.call_count, 1)
        mock_maya.refresh.side_effect = ValueError("Error")
        AzureBatchPools.update_pool(self.mock_self, 0)
        self.assertEqual(self.mock_self.ui.refresh.call_count, 2)

    def test_pools_auto_pool(self):
        self.mock_self.pools = [mock.Mock(id='Maya_Pool_123'), mock.Mock(id='Maya_Auto_Pool_123')]
        self.mock_self.selected_pool = mock.Mock(index=1)
        self.assertTrue(AzureBatchPools.is_auto_pool(self.mock_self))
        self.mock_self.selected_pool = mock.Mock(index=0)
        self.assertFalse(AzureBatchPools.is_auto_pool(self.mock_self))
        self.mock_self.selected_pool = mock.Mock(index=2)
        self.assertFalse(AzureBatchPools.is_auto_pool(self.mock_self))

    def test_pools_get_size(self):

        self.mock_self.pools = [mock.Mock(target_dedicated_nodes=5),
                                mock.Mock(target_dedicated_nodes="8"),
                                mock.Mock(target_dedicated_nodes=None)]

        self.mock_self.selected_pool = mock.Mock(index=0)
        self.assertEqual(AzureBatchPools.get_pool_size(self.mock_self), 5)

        self.mock_self.selected_pool = mock.Mock(index=1)
        self.assertEqual(AzureBatchPools.get_pool_size(self.mock_self), 8)

        self.mock_self.selected_pool = mock.Mock(index=2)
        self.assertEqual(AzureBatchPools.get_pool_size(self.mock_self), 0)

        self.mock_self.selected_pool = mock.Mock(index=3)
        self.assertEqual(AzureBatchPools.get_pool_size(self.mock_self), 0)

    def test_pools_delete(self):

        mock_pool = mock.create_autospec(models.CloudPool)
        mock_pool.id = "pool id"
        self.mock_self.pools = [mock_pool]

        def call(func, *args):
            self.assertTrue(callable(func))
            return func(*args)

        self.mock_self._call = call
        self.mock_self.selected_pool = mock.Mock(index=0)
        self.mock_self.ui = mock.create_autospec(PoolsUI)

        AzureBatchPools.delete_pool(self.mock_self)
        self.assertEqual(self.mock_self.ui.refresh.call_count, 1)
        self.mock_self.batch.pool.delete.assert_called_with("pool id")

        self.mock_self.batch.pool.delete.side_effect = AttributeError("boom")
        AzureBatchPools.delete_pool(self.mock_self)
        self.assertEqual(self.mock_self.ui.refresh.call_count, 2)
        self.mock_self.batch.pool.delete.assert_called_with("pool id")

        self.mock_self.selected_pool.index = 1
        AzureBatchPools.delete_pool(self.mock_self)
        self.assertEqual(self.mock_self.ui.refresh.call_count, 3)
        self.assertEqual(self.mock_self.batch.pool.delete.call_count, 2)

    def test_pools_create(self):
        pool_obj = None
        def call(func, new_pool):
            global pool_obj
            self.assertTrue(callable(func))
            pool_obj = new_pool
            self.assertEqual(new_pool.target_dedicated_nodes, 5)
            self.assertEqual(new_pool.display_name, "Maya Pool for test job")
            self.assertEqual(new_pool.application_licenses, ['maya'])
            self.assertEqual(new_pool.virtual_machine_configuration.node_agent_sku_id, 'sku_id')
            self.assertEqual(new_pool.virtual_machine_configuration.image_reference.publisher, 'foo')
            return func(new_pool)

        self.mock_self._call = call
        self.mock_self.environment.get_application_licenses.return_value = ['maya']
        self.mock_self.environment.get_image.return_value = {
            'publisher': 'foo', 'sku': 'bar', 'offer': 'baz', 'node_sku_id':'sku_id'}
        AzureBatchPools.create_pool(self.mock_self, 5, "test job")
        self.mock_self.batch.pool.add.assert_called_with(mock.ANY)

    @mock.patch("pools.maya")
    def test_pools_resize(self, mock_maya):

        def call(func, *args):
            self.assertTrue(callable(func))
            self.assertEqual(args[1]['target_dedicated_nodes'], 5)
            return func(*args)

        mock_pool = mock.create_autospec(models.CloudPool)
        mock_pool.id = "pool id"
        self.mock_self.pools = [mock_pool]

        self.mock_self._call = call
        self.mock_self.selected_pool = mock.Mock(index=0)
        self.mock_self.ui = mock.create_autospec(PoolsUI)

        AzureBatchPools.resize_pool(self.mock_self, 5)
        self.assertFalse(self.mock_self.ui.refresh.call_count)

        AzureBatchPools.resize_pool(self.mock_self, "5")
        self.assertFalse(self.mock_self.ui.refresh.call_count)

        AzureBatchPools.resize_pool(self.mock_self, None)
        self.assertEqual(self.mock_self.ui.refresh.call_count, 1)
