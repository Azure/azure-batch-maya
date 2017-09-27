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

from azurebatchutils import ProgressBar
from ui_submission import SubmissionUI
from ui_shared import AzureBatchUI
from submission import AzureBatchSubmission, AzureBatchRenderJob
from assets import AzureBatchAssets
from pools import AzureBatchPools
from environment import AzureBatchEnvironment
from shared import AzureBatchSettings
from exception import CancellationException
from azurebatchutils import OperatingSystem

from azure.batch_extensions import BatchExtensionsClient
from azure.batch.batch_auth import SharedKeyCredentials
from azure.batch_extensions import operations
from azure.batch_extensions import models

from azure.storage.blob import BlockBlobService


def print_status(status):
    print(status)


class TestBatchSubmission(unittest.TestCase):
    
    def setUp(self):
        test_dir = os.path.dirname(__file__)
        top_dir = os.path.dirname(test_dir)
        src_dir = os.path.join(top_dir, 'azure_batch_maya', 'scripts')
        mod_dir = os.path.join(test_dir, 'data', 'modules')
        ui_dir = os.path.join(src_dir, 'ui')
        tools_dir = os.path.join(src_dir, 'tools')
        os.environ["AZUREBATCH_ICONS"] = os.path.join(top_dir, 'azure_batch_maya', 'icons')
        os.environ["AZUREBATCH_TEMPLATES"] = os.path.join(top_dir, 'azure_batch_maya', 'templates')
        os.environ["AZUREBATCH_MODULES"] = mod_dir
        os.environ["AZUREBATCH_SCRIPTS"] = "{0};{1};{2}".format(src_dir, ui_dir, tools_dir)
        os.environ["AZUREBATCH_VERSION"] = "0.1"
        self.mock_self = mock.create_autospec(AzureBatchSubmission)
        self.mock_self.batch = mock.create_autospec(BatchExtensionsClient)
        self.mock_self.batch.job = mock.create_autospec(operations.ExtendedJobOperations)
        self.mock_self.batch.job.jobparameter_from_json.return_value = \
            mock.create_autospec(models.ExtendedJobParameter)
        self.mock_self.ui = mock.create_autospec(SubmissionUI)
        self.mock_self.ui.submit_status = print_status
        self.mock_self.pool_manager = mock.create_autospec(AzureBatchPools)
        self.mock_self.asset_manager = mock.create_autospec(AzureBatchAssets)
        self.mock_self.env_manager = mock.create_autospec(AzureBatchEnvironment)
        self.mock_self._log = logging.getLogger("TestSubmission")
        self.mock_self.renderer = None
        self.mock_self.frame = mock.create_autospec(AzureBatchUI)
        return super(TestBatchSubmission, self).setUp()

    @mock.patch.object(AzureBatchSubmission, "_collect_modules")
    @mock.patch("submission.callback")
    @mock.patch("submission.SubmissionUI")
    def test_submission_create(self, mock_ui, mock_call, mock_mods):
        submission = AzureBatchSubmission(2, "frame", "call")
        mock_mods.assert_called_with()
        mock_ui.assert_called_with(submission, "frame")
        #mock_call.after_new.assert_called_with(mock.ANY)
        #mock_call.after_open.assert_called_with(mock.ANY)

    @mock.patch("submission.maya")
    def test_submission_start(self, mock_maya):
        session = mock.Mock(batch="batch_client", storage="storage_client")
        self.mock_self.ui = mock.create_autospec(SubmissionUI)
        self.mock_self.ui.render_module = "module"
        self.mock_self.renderer = mock.Mock()
        AzureBatchSubmission.start(self.mock_self, session, "assets", "pools", "env")
        self.mock_self.renderer.delete.assert_called_with()
        self.mock_self._configure_renderer.assert_called_with()
        self.mock_self.renderer.display.assert_called_with("module")
        self.mock_self.ui.is_logged_in.assert_called_with()

    def test_submission_collect_modules(self):
        mods = AzureBatchSubmission._collect_modules(self.mock_self)
        self.assertEqual(len(mods), 4)

    @mock.patch("submission.AzureBatchRenderJob")
    @mock.patch("submission.maya")
    def test_submission_configure_renderer(self, mock_maya, mock_default):
        mock_default.return_value = mock.Mock(render_engine = "default")
        mock_maya.get_attr.return_value = "test_renderer"

        renderer = mock.Mock(render_engine = "my_renderer")
        self.mock_self.modules = [renderer, "test", None]

        AzureBatchSubmission._configure_renderer(self.mock_self)
        self.assertEqual(self.mock_self.renderer.render_engine, "default")

        renderer = mock.Mock(render_engine = "test_renderer")
        self.mock_self.modules.append(renderer)

        AzureBatchSubmission._configure_renderer(self.mock_self)
        self.assertEqual(self.mock_self.renderer.render_engine, "test_renderer")

    def test_submission_refresh_renderer(self):
        self.mock_self.ui = mock.create_autospec(SubmissionUI)
        self.mock_self.renderer = mock.Mock()
        AzureBatchSubmission.refresh_renderer(self.mock_self, "layout")
        self.mock_self.renderer.delete.assert_called_with()
        self.mock_self.renderer.display.assert_called_with("layout")

    def test_submission_available_pools(self):
        def list_pools(**kwargs):
            self.assertTrue(kwargs.get("lazy"))
            return ["pool1", "pool2"]
        self.mock_self.pool_manager = mock.Mock(list_pools=list_pools)
        pools = AzureBatchSubmission.available_pools(self.mock_self)
        self.assertEqual(pools, ["pool1", "pool2"])

    @mock.patch("submission.utils")
    @mock.patch("submission.maya")
    def test_submission_submit(self, mock_maya, mock_utils):
        def call(func, *args, **kwargs):
            self.assertTrue(callable(func))
            return func(*args, **kwargs)

        mock_prog = mock.create_autospec(ProgressBar)
        mock_prog.is_cancelled.return_value = False
        mock_utils.ProgressBar.return_value = mock_prog
        mock_utils.format_scene_path.return_value = "test_file_path"
        self.mock_self._configure_pool = lambda t: AzureBatchSubmission._configure_pool(self.mock_self, t)
        self.mock_self._submit_threads = lambda: 6
        self.mock_self._check_plugins.return_value = []
        self.mock_self._get_os_flavor.return_value = OperatingSystem.windows
        self.mock_self.pool_manager.create_auto_pool.return_value = {'autoPool': 'auto-pool'}
        self.mock_self.pool_manager.create_pool.return_value = {'poolId': 'new-pool'}
        self.mock_self.env_manager.get_environment_settings.return_value = [{'name':'foo', 'value':'bar'}]
        self.mock_self.renderer = mock.Mock(render_engine='arnold')
        self.mock_self.renderer.get_jobdata.return_value = ("a", "b")
        self.mock_self.renderer.get_params.return_value = {"foo": "bar"}
        self.mock_self.renderer.get_title.return_value = "job name"
        self.mock_self._call = call
        mock_job = mock.create_autospec(models.ExtendedJobParameter)
        self.mock_self.batch.job.jobparameter_from_json.return_value = mock_job
        self.mock_self.asset_manager.upload.return_value = ("files", "maps", "thumbs", "workspace", mock_prog)
        self.mock_self.asset_manager.generate_sas_token.return_value = "0123456789ABCDEF"
        self.mock_self.batch.threads = 6

        self.mock_self.ui.get_pool.return_value = {1: (4, 4)}
        AzureBatchSubmission.submit(self.mock_self)
        self.assertEqual(mock_maya.error.call_count, 0)
        self.mock_self.renderer.disable.assert_called_with(True)
        self.mock_self.pool_manager.create_auto_pool.assert_called_with((4, 4), "job name")
        self.mock_self.batch.job.add.assert_called_with(mock_job)
        self.mock_self.batch.job.jobparameter_from_json.assert_called_with(
            {'commonEnvironmentSettings': [{'name': 'foo', 'value':'bar'}],
             'poolInfo': {'autoPool': 'auto-pool'},
             'displayName': 'job name',
             'id': mock.ANY,
             'applicationTemplateInfo': {
                 'parameters': {'sceneFile': 'test_file_path', 'outputs': mock.ANY, 'assetScript': 'maps', 'foo': 'bar',
                                'projectData': 'files', 'thumbScript': 'thumbs', 'storageURL': '0123456789ABCDEF', 'workspace': 'workspace'},
                 'filePath': os.path.join(os.environ['AZUREBATCH_TEMPLATES'], 'arnold-basic-windows.json')},
             'metadata': [{'name': 'JobType', 'value': 'Maya'}]})


        self.mock_self.ui.get_pool.return_value = {2:4}
        AzureBatchSubmission.submit(self.mock_self)
        self.assertEqual(mock_maya.error.call_count, 0)
        self.mock_self.renderer.disable.assert_called_with(True)
        self.mock_self.batch.job.add.assert_called_with(mock_job)
        self.mock_self.batch.job.jobparameter_from_json.assert_called_with(
            {'commonEnvironmentSettings': [{'name': 'foo', 'value':'bar'}],
             'poolInfo': {'poolId': '4'},
             'displayName': 'job name',
             'id': mock.ANY,
             'applicationTemplateInfo': {
                 'parameters': {'sceneFile': 'test_file_path', 'outputs': mock.ANY, 'assetScript': 'maps', 'foo': 'bar',
                                'projectData': 'files', 'thumbScript': 'thumbs', 'storageURL': '0123456789ABCDEF', 'workspace': 'workspace'},
                 'filePath': os.path.join(os.environ['AZUREBATCH_TEMPLATES'], 'arnold-basic-windows.json')},
             'metadata': [{'name': 'JobType', 'value': 'Maya'}]})


        self.mock_self._check_outputs.side_effect = ValueError("No camera")
        AzureBatchSubmission.submit(self.mock_self)
        self.assertEqual(mock_maya.error.call_count, 1)
        self.mock_self._check_outputs.side_effect = None

        self.mock_self.ui.get_pool.return_value = {3: (4, 4)}
        AzureBatchSubmission.submit(self.mock_self)
        self.assertEqual(mock_maya.error.call_count, 1)
        self.mock_self.renderer.disable.assert_called_with(True)

        self.mock_self.batch.job.add.assert_called_with(mock_job)
        self.mock_self.batch.job.add.call_count = 0
        self.mock_self.pool_manager.create_pool.assert_called_with((4, 4), 'job name')

        mock_prog.is_cancelled.side_effect = CancellationException("cancelled")
        AzureBatchSubmission.submit(self.mock_self)
        self.assertEqual(mock_maya.info.call_count, 4)
        self.mock_self.renderer.disable.assert_called_with(True)
        self.assertEqual(self.mock_self.batch.job.add.call_count, 0)

        mock_prog.is_cancelled.side_effect = None
        self.mock_self.pool_manager.create_pool.side_effect = ValueError("Bad data")
        AzureBatchSubmission.submit(self.mock_self)
        self.assertEqual(mock_maya.error.call_count, 2)
        self.mock_self.renderer.disable.assert_called_with(True)
        self.assertEqual(self.mock_self.batch.job.add.call_count, 0)
