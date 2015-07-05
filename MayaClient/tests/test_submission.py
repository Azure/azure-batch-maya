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

from utils import ProgressBar
from ui_submission import SubmissionUI
from ui_shared import BatchAppsUI
from submission import BatchAppsSubmission, BatchAppsRenderJob
from batchapps import JobManager, Configuration, Credentials
from batchapps.job import SubmittedJob, JobSubmission, Task
from batchapps.exceptions import SessionExpiredException

from assets import BatchAppsAssets
from pools import BatchAppsPools
from environment import BatchAppsEnvironment

class TestBatchAppsSubmission(unittest.TestCase):
    
    def setUp(self):
        self.mock_self = mock.create_autospec(BatchAppsSubmission)
        self.mock_self._log = logging.getLogger("TestSubmission")
        self.mock_self.renderer = None
        self.mock_self.frame = mock.create_autospec(BatchAppsUI)

        return super(TestBatchAppsSubmission, self).setUp()

    @mock.patch.object(BatchAppsSubmission, "collect_modules")
    @mock.patch("submission.callback")
    @mock.patch("submission.SubmissionUI")
    def test_create_batchappssubmission(self, mock_ui, mock_call, mock_mods):

        submission = BatchAppsSubmission("frame", "call")
        mock_mods.assert_called_with()
        mock_ui.assert_called_with(submission, "frame")
        mock_call.after_new.assert_called_with(mock.ANY)
        mock_call.after_open.assert_called_with(mock.ANY)

    @mock.patch("submission.JobManager")
    @mock.patch("submission.maya")
    def test_start(self, mock_maya, mock_mgr):

        session = mock.Mock(credentials="creds", config="conf")
        self.mock_self.ui = mock.create_autospec(SubmissionUI)
        self.mock_self.ui.render_module = "module"
        self.mock_self.renderer = mock.Mock()
        
        BatchAppsSubmission.start(self.mock_self, session, "assets", "pools", "env")
        mock_mgr.assert_called_with("creds", "conf")
        self.mock_self.renderer.delete.assert_called_with()
        self.mock_self.configure_renderer.assert_called_with()
        self.mock_self.renderer.display.assert_called_with("module")
        self.mock_self.ui.is_logged_in.assert_called_with()

    def test_collect_modules(self):

        mods = BatchAppsSubmission.collect_modules(self.mock_self)
        self.assertEqual(len(mods), 4)

    @mock.patch("submission.BatchAppsRenderJob")
    @mock.patch("submission.maya")
    def test_configure_renderer(self, mock_maya, mock_default):

        mock_default.return_value = mock.Mock(render_engine = "default")
        mock_maya.mel.return_value = "test_renderer"

        renderer = mock.Mock(render_engine = "my_renderer")
        self.mock_self.modules = [renderer, "test", None]

        BatchAppsSubmission.configure_renderer(self.mock_self)
        self.assertEqual(self.mock_self.renderer, mock_default.return_value)

        renderer = mock.Mock(render_engine = "test_renderer")
        self.mock_self.modules.append(renderer)

        BatchAppsSubmission.configure_renderer(self.mock_self)
        self.assertEqual(self.mock_self.renderer, renderer)

    def test_refresh_renderer(self):

        self.mock_self.ui = mock.create_autospec(SubmissionUI)
        self.mock_self.renderer = mock.Mock()

        BatchAppsSubmission.refresh_renderer(self.mock_self, "layout")
        self.mock_self.renderer.delete.assert_called_with()
        self.mock_self.renderer.display.assert_called_with("layout")

    def test_available_pools(self):

        def list_pools(**kwargs):
            self.assertTrue(kwargs.get("lazy"))
            return ["pool1", "pool2"]

        self.mock_self.pool_manager = mock.Mock(list_pools=list_pools)
        pools = BatchAppsSubmission.available_pools(self.mock_self)
        self.assertEqual(pools, ["pool1", "pool2"])

    @mock.patch("submission.utils")
    @mock.patch("submission.maya")
    def test_submit(self, mock_maya, mock_utils):
        
        def call(func):
            self.assertTrue(hasattr(func, '__call__'))
            return func()

        mock_prog = mock.create_autospec(ProgressBar)
        mock_prog.is_cancelled.return_value = False
        mock_utils.ProgressBar.return_value = mock_prog
        #self.mock_self.configure_environment = lambda a,b:BatchAppsSubmission.configure_environment(self.mock_self, a,b)
        self.mock_self.configure_pool = lambda a: BatchAppsSubmission.configure_pool(self.mock_self, a)
        self.mock_self.check_outputs.return_value = None
        self.mock_self.job_manager = mock.create_autospec(JobManager)
        job = mock.create_autospec(JobSubmission)
        job.required_files = mock.Mock()
        job.required_files.upload.return_value = None

        self.mock_self.job_manager.create_job.return_value = job
        self.mock_self.ui = mock.create_autospec(SubmissionUI)
        self.mock_self.pool_manager = mock.Mock()
        self.mock_self.asset_manager = mock.Mock()
        self.mock_self.renderer = mock.Mock()
        self.mock_self._call = call

        self.mock_self.ui.get_pool.return_value = {1:"pool"}
        self.mock_self.asset_manager.upload.return_value = ("files", "maps", mock_prog)

        BatchAppsSubmission.submit(self.mock_self)
        self.assertEqual(mock_maya.error.call_count, 1)
        self.mock_self.renderer.disable.assert_called_with(True)
        self.mock_self.ui.processing.assert_called_with(True)

        self.mock_self.ui.get_pool.return_value = {1:4}

        BatchAppsSubmission.submit(self.mock_self)
        self.assertEqual(mock_maya.error.call_count, 1)
        self.mock_self.renderer.disable.assert_called_with(True)
        self.mock_self.ui.processing.assert_called_with(True)

        job.submit.assert_called_with()
        self.assertEqual(job.instances, 4)

        self.mock_self.ui.get_pool.return_value = {2:4}
        BatchAppsSubmission.submit(self.mock_self)
        self.assertEqual(mock_maya.error.call_count, 1)
        self.mock_self.renderer.disable.assert_called_with(True)
        self.mock_self.ui.processing.assert_called_with(True)

        job.submit.assert_called_with()
        self.assertEqual(job.pool, '4')

        self.mock_self.check_outputs.side_effect = ValueError("No camera")
        BatchAppsSubmission.submit(self.mock_self)
        self.assertEqual(mock_maya.error.call_count, 2)
        self.mock_self.check_outputs.side_effect = None

        self.mock_self.ui.get_pool.return_value = {3: 4}
        BatchAppsSubmission.submit(self.mock_self)
        self.assertEqual(mock_maya.error.call_count, 2)
        self.mock_self.renderer.disable.assert_called_with(True)
        self.mock_self.ui.processing.assert_called_with(True)

        job.submit.assert_called_with()
        job.submit.call_count = 0
        self.mock_self.pool_manager.create_pool.assert_called_with(4)

        mock_prog.is_cancelled.return_value = True
        BatchAppsSubmission.submit(self.mock_self)
        self.assertEqual(mock_maya.info.call_count, 4)
        self.mock_self.renderer.disable.assert_called_with(True)
        self.mock_self.ui.processing.assert_called_with(True)
        self.assertEqual(job.submit.call_count, 0)

        mock_prog.is_cancelled.return_value = False
        self.mock_self.pool_manager.create_pool.side_effect = SessionExpiredException("Logged out!")
        BatchAppsSubmission.submit(self.mock_self)
        self.assertEqual(mock_maya.error.call_count, 2)
        self.mock_self.renderer.disable.assert_called_with(True)
        self.mock_self.ui.processing.assert_called_with(True)
        self.assertEqual(job.submit.call_count, 0)


#class TestSubmissionCombined(unittest.TestCase):

#    @mock.patch("ui_submission.utils")
#    @mock.patch("ui_submission.maya")
#    @mock.patch("submission.callback")
#    @mock.patch("submission.maya")
#    def test_submission(self, *args):

#        mock_callback = args[1]
#        mock_maya = args[0]
#        mock_maya.mel.return_value = "Renderer"
#        mock_maya.get_list.return_value = ["1","2","3"]
#        mock_maya.get_attr.return_value = True

#        ui_maya = args[2]
#        ui_maya.radio_group.return_value = 2
#        ui_maya.menu.return_value = "12345"
#        ui_maya.int_slider.return_value = 6

#        def add_tab(tab):
#            pass

#        def call(func, *args, **kwargs):
#            self.assertTrue(hasattr(func, '__call__'))
#            return func()
        
#        layout = mock.Mock(add_tab=add_tab)
#        sub = BatchAppsSubmission(layout, call)
#        self.assertEqual(len(sub.modules), 4)
#        self.assertTrue(mock_callback.after_new.called)
#        self.assertTrue(mock_callback.after_open.called)

#        creds = mock.create_autospec(Credentials)
#        conf = mock.create_autospec(Configuration)
#        session = mock.Mock(credentials=creds, config=conf)
#        assets = mock.create_autospec(BatchAppsAssets)
#        pools = mock.create_autospec(BatchAppsPools)
#        env = mock.create_autospec(BatchAppsEnvironment)

#        sub.start(session, assets, pools, env)
        
#        mock_maya.mel.return_value = "Renderer_A"
#        sub.ui.refresh()

#        sub.asset_manager.collect_assets.return_value = {'assets':['abc'],
#                                                         'pathmaps':'mapping'}
#        sub.job_manager = mock.create_autospec(JobManager)
#        job = mock.create_autospec(JobSubmission)
#        job.required_files = mock.Mock()
#        job.required_files.upload.return_value = []
#        sub.job_manager.create_job.return_value = job

#        sub.submit()
#        self.assertEqual(mock_maya.error.call_count, 0)
#        self.assertEqual(sub.pool_manager.create_pool.call_count, 0)
#        job.submit.assert_called_with()
#        self.assertEqual(job.params, {"setting_A":1, "setting_B":2})
#        job.add_file_collection.assert_called_with(["abc"])
#        self.assertEqual(job.pool, "12345")

#        mock_maya.get_attr.return_value = False
#        sub.submit()
#        mock_maya.error.assert_called_with(mock.ANY)
#        mock_maya.error.call_count = 0
#        mock_maya.get_attr.return_value = True

#        ui_maya.menu.return_value = None
#        sub.submit()
#        mock_maya.error.assert_called_with("No pool selected.")
#        mock_maya.error.call_count = 0

#        ui_maya.radio_group.return_value = 1
#        sub.submit()
#        self.assertEqual(mock_maya.error.call_count, 0)
#        self.assertEqual(sub.pool_manager.create_pool.call_count, 0)
#        job.submit.assert_called_with()
#        self.assertEqual(job.instances, 6)

#        ui_maya.radio_group.return_value = 3
#        sub.submit()
#        self.assertEqual(mock_maya.error.call_count, 0)
#        sub.pool_manager.create_pool.assert_called_with(6)
#        job.submit.assert_called_with()

#        job.required_files.upload.return_value = [("failed", Exception("boom"))]
#        sub.submit()
#        self.assertEqual(mock_maya.error.call_count, 1)