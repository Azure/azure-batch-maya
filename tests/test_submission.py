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

from utils import ProgressBar
from ui_submission import SubmissionUI
from ui_shared import AzureBatchUI
from submission import AzureBatchSubmission, AzureBatchRenderJob
from assets import AzureBatchAssets
from pools import AzureBatchPools
from environment import AzureBatchEnvironment

from batch_extensions import BatchExtensionsClient
from batch_extensions import operations
from batch_extensions import models

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
        self.mock_self = mock.create_autospec(AzureBatchSubmission)
        self.mock_self.batch = mock.create_autospec(BatchExtensionsClient)
        self.mock_self.batch.job = mock.create_autospec(operations.ExtendedJobOperations)
        self.mock_self.batch.job.jobparameter_from_json.return_value = \
            mock.create_autospec(models.ExtendedJobParameter)
        self.mock_self.ui = mock.create_autospec(SubmissionUI)
        self.mock_self.ui.submit_status = print_status
        self.mock_self.pool_manager = mock.create_autospec(AzureBatchPools)
        self.mock_self.asset_manager = mock.create_autospec(AzureBatchAssets)
        self.mock_self._log = logging.getLogger("TestSubmission")
        self.mock_self.renderer = None
        self.mock_self.frame = mock.create_autospec(AzureBatchUI)
        return super(TestBatchSubmission, self).setUp()

    @mock.patch.object(AzureBatchSubmission, "_collect_modules")
    @mock.patch("submission.callback")
    @mock.patch("submission.SubmissionUI")
    def test_submission_create(self, mock_ui, mock_call, mock_mods):
        submission = AzureBatchSubmission("frame", "call")
        mock_mods.assert_called_with()
        mock_ui.assert_called_with(submission, "frame")
        mock_call.after_new.assert_called_with(mock.ANY)
        mock_call.after_open.assert_called_with(mock.ANY)

    @mock.patch("submission.maya")
    def test_submission_start(self, mock_maya):
        session = mock.Mock(batch="batch_client", storage="storage_client")
        self.mock_self.ui = mock.create_autospec(SubmissionUI)
        self.mock_self.ui.render_module = "module"
        self.mock_self.renderer = mock.Mock()
        AzureBatchSubmission.start(self.mock_self, session, "assets", "pools")
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
        def call(func):
            self.assertTrue(hasattr(func, '__call__'))
            return func()

        mock_prog = mock.create_autospec(ProgressBar)
        mock_prog.is_cancelled.return_value = False
        mock_utils.ProgressBar.return_value = mock_prog
        self.mock_self._configure_pool = AzureBatchSubmission._configure_pool
        self.mock_self._check_outputs = AzureBatchSubmission._check_outputs
        self.mock_self._check_plugins.return_value = []
        self.mock_self.asset_manager.upload.return_value = ("a", "b", mock_prog)
        self.mock_self.pool_manager.create_auto_pool.return_value = {'autoPool': 'auto-pool'}
        self.mock_self.pool_manager.create_pool.return_value = {'poolId': 'new-pool'}
        self.mock_self.renderer = mock.Mock()
        self.mock_self.renderer.get_jobdata.return_value = ("a", "b")
        self.mock_self.renderer.get_params.return_value = {"foo": "bar"}
        self.mock_self.renderer.get_title.return_value = "job name"
        self.mock_self._call = call

        self.mock_self.ui.get_pool.return_value = {1:"pool"}
        self.mock_self.asset_manager.upload.return_value = ("files", "maps", mock_prog)

        AzureBatchSubmission.submit(self.mock_self)
        self.assertEqual(mock_maya.error.call_count, 1)
        self.mock_self.renderer.disable.assert_called_with(True)

        self.mock_self.ui.get_pool.return_value = {1:4}

        AzureBatchSubmission.submit(self.mock_self)
        self.assertEqual(mock_maya.error.call_count, 1)
        self.mock_self.renderer.disable.assert_called_with(True)

        job.submit.assert_called_with()
        self.assertEqual(job.instances, 4)

        self.mock_self.ui.get_pool.return_value = {2:4}
        AzureBatchSubmission.submit(self.mock_self)
        self.assertEqual(mock_maya.error.call_count, 1)
        self.mock_self.renderer.disable.assert_called_with(True)

        job.submit.assert_called_with()
        self.assertEqual(job.pool, '4')

        self.mock_self.check_outputs.side_effect = ValueError("No camera")
        AzureBatchSubmission.submit(self.mock_self)
        self.assertEqual(mock_maya.error.call_count, 2)
        self.mock_self.check_outputs.side_effect = None

        self.mock_self.ui.get_pool.return_value = {3: 4}
        AzureBatchSubmission.submit(self.mock_self)
        self.assertEqual(mock_maya.error.call_count, 2)
        self.mock_self.renderer.disable.assert_called_with(True)

        job.submit.assert_called_with()
        job.submit.call_count = 0
        self.mock_self.pool_manager.create_pool.assert_called_with(4)

        mock_prog.is_cancelled.return_value = True
        AzureBatchSubmission.submit(self.mock_self)
        self.assertEqual(mock_maya.info.call_count, 4)

        self.mock_self.renderer.disable.assert_called_with(True)
        self.assertEqual(job.submit.call_count, 0)

        mock_prog.is_cancelled.return_value = False
        self.mock_self.pool_manager.create_pool.side_effect = Exception("Logged out!")
        AzureBatchSubmission.submit(self.mock_self)
        self.assertEqual(mock_maya.error.call_count, 3)
        self.mock_self.renderer.disable.assert_called_with(True)
        self.assertEqual(job.submit.call_count, 0)


class TestSubmissionCombined(unittest.TestCase):

    @mock.patch("submission.utils")
    @mock.patch("ui_submission.utils")
    @mock.patch("ui_submission.maya")
    @mock.patch("submission.callback")
    @mock.patch("submission.maya")
    def test_submission(self, *args):

        mock_callback = args[1]
        mock_maya = args[0]
        mock_maya.mel.return_value = "Renderer"
        mock_maya.get_list.return_value = ["1","2","3"]
        mock_maya.get_attr.return_value = True

        ui_maya = args[2]
        ui_maya.radio_group.return_value = 2
        ui_maya.menu.return_value = "12345"
        ui_maya.int_slider.return_value = 6

        def add_tab(tab):
            pass

        def call(func, *args, **kwargs):
            self.assertTrue(hasattr(func, '__call__'))
            return func()
        
        mock_utils = args[4]
        mock_prog = mock.create_autospec(ProgressBar)
        mock_prog.is_cancelled.return_value = False
        mock_utils.ProgressBar.return_value = mock_prog

        layout = mock.Mock(add_tab=add_tab)
        sub = AzureBatchSubmission(layout, call)
        self.assertEqual(len(sub.modules), 4)
        self.assertTrue(mock_callback.after_new.called)
        self.assertTrue(mock_callback.after_open.called)

        creds = mock.create_autospec(Credentials)
        conf = mock.create_autospec(Configuration)
        session = mock.Mock(credentials=creds, config=conf)
        assets = mock.create_autospec(BatchAppsAssets)
        pools = mock.create_autospec(BatchAppsPools)
        env = mock.create_autospec(BatchAppsEnvironment)
        env.license = {"license":"test"}
        env.environment_variables = {"env":"val"}
        env.plugins = {"plugins":"test"}

        sub.start(session, assets, pools, env)
        
        mock_maya.mel.return_value = "Renderer_A"
        sub.ui.refresh()

        sub.asset_manager.upload.return_value = (["abc"], {}, mock_prog)
        sub.asset_manager.collect_assets.return_value = {'assets':['abc'],
                                                         'pathmaps':'mapping'}
        sub.job_manager = mock.create_autospec(JobManager)
        job = mock.create_autospec(JobSubmission)
        job.required_files = mock.Mock()
        job.required_files.upload.return_value = []
        sub.job_manager.create_job.return_value = job

        sub.submit()
        self.assertEqual(mock_maya.error.call_count, 0)
        self.assertEqual(sub.pool_manager.create_pool.call_count, 0)
        job.submit.assert_called_with()
        self.assertEqual(job.params, {"setting_A":1, "setting_B":2})
        job.add_file_collection.assert_called_with(["abc"])
        self.assertEqual(job.pool, "12345")

        mock_maya.get_attr.return_value = False
        sub.submit()
        mock_maya.error.assert_called_with(mock.ANY)
        mock_maya.error.call_count = 0
        mock_maya.get_attr.return_value = True

        ui_maya.menu.return_value = None
        sub.submit()
        mock_maya.error.assert_called_with("No pool selected.")
        mock_maya.error.call_count = 0

        ui_maya.radio_group.return_value = 1
        sub.submit()
        self.assertEqual(mock_maya.error.call_count, 0)
        self.assertEqual(sub.pool_manager.create_pool.call_count, 0)
        job.submit.assert_called_with()
        self.assertEqual(job.instances, 6)

        ui_maya.radio_group.return_value = 3
        sub.submit()
        self.assertEqual(mock_maya.error.call_count, 0)
        sub.pool_manager.create_pool.assert_called_with(6)
        job.submit.assert_called_with()

        sub.asset_manager.upload.return_value = [("failed", Exception("boom"))]
        sub.submit()
        self.assertEqual(mock_maya.error.call_count, 1)
