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

from ui_history import HistoryUI, BatchAppsJobInfo
from history import BatchAppsHistory
from batchapps import JobManager, Configuration, Credentials
from batchapps.job import SubmittedJob, JobSubmission, Task
from batchapps.exceptions import FileDownloadException
from utils import ProcButton

class TestBatchAppsHistory(unittest.TestCase):
    
    def setUp(self):
        self.mock_self = mock.create_autospec(BatchAppsHistory)
        self.mock_self._log = logging.getLogger("TestHistory")
        self.mock_self.index = 0
        self.mock_self.per_call = 5
        self.mock_self.min = True
        self.mock_self.max = False
        return super(TestBatchAppsHistory, self).setUp()

    @mock.patch("history.HistoryUI")
    def test_create_batchappshistory(self, mock_ui):

        history = BatchAppsHistory("frame", "call")
        mock_ui.assert_called_with(history, "frame")

    @mock.patch("history.JobManager")
    def test_configure(self, mock_mgr):

        session = mock.Mock(credentials="creds", config="conf")
        BatchAppsHistory.configure(self.mock_self, session)

        mock_mgr.assert_called_with("creds", "conf")
        self.assertEqual(session, self.mock_self._session)

    def test_get_history(self):

        mgr = mock.create_autospec(JobManager)
        mgr.get_jobs.return_value = [mock.Mock(name="test_job")]
        mgr.__len__.return_value = 1

        def call(func, arg_a, arg_b):
            self.assertEqual(func, mgr.get_jobs)
            self.assertEqual(arg_a, 0)
            self.assertEqual(arg_b, 5)
            return func()

        self.mock_self.manager = mgr
        self.mock_self._call = call
        self.mock_self.ui = mock.create_autospec(HistoryUI)
        self.mock_self.ui.create_job_entry.return_value = "job_entry"

        displayed = BatchAppsHistory.get_history(self.mock_self)
        self.assertEqual(displayed, ["job_entry"])
        self.assertEqual(len(self.mock_self.jobs), 1)

    def test_set_num_jobs(self):

        self.mock_self.ui = mock.create_autospec(HistoryUI)
        self.mock_self.count = 8

        BatchAppsHistory.set_num_jobs(self.mock_self)
        self.assertEqual(self.mock_self.ui.num_jobs, "1 - 5 of 8")

        self.mock_self.count = 3
        BatchAppsHistory.set_num_jobs(self.mock_self)
        self.assertEqual(self.mock_self.ui.num_jobs, "1 - 3 of 3")

        self.mock_self.index = 5
        BatchAppsHistory.set_num_jobs(self.mock_self)
        self.assertEqual(self.mock_self.ui.num_jobs, "3 - 3 of 3")

        self.mock_self.count = 20
        BatchAppsHistory.set_num_jobs(self.mock_self)
        self.assertEqual(self.mock_self.ui.num_jobs, "6 - 10 of 20")

    def test_set_min_max(self):

        self.mock_self.ui = mock.create_autospec(HistoryUI)
        self.mock_self.count = 4
        BatchAppsHistory.set_min_max(self.mock_self)
        self.assertTrue(self.mock_self.min)
        self.assertTrue(self.mock_self.max)

        self.mock_self.index = 2
        BatchAppsHistory.set_min_max(self.mock_self)
        self.assertTrue(self.mock_self.max)
        self.assertFalse(self.mock_self.min)

        self.mock_self.count = 20
        BatchAppsHistory.set_min_max(self.mock_self)
        self.assertFalse(self.mock_self.max)
        self.assertFalse(self.mock_self.min)

        self.mock_self.count = 5
        BatchAppsHistory.set_min_max(self.mock_self)
        self.assertTrue(self.mock_self.max)
        self.assertFalse(self.mock_self.min)

        self.mock_self.count = 6
        BatchAppsHistory.set_min_max(self.mock_self)
        self.assertFalse(self.mock_self.max)
        self.assertFalse(self.mock_self.min)

    def test_next_jobs(self):

        self.mock_self.count = 12
        BatchAppsHistory.show_next_jobs(self.mock_self)
        self.assertEqual(self.mock_self.index, 5)

        BatchAppsHistory.show_next_jobs(self.mock_self)
        self.assertEqual(self.mock_self.index, 10)

        BatchAppsHistory.show_next_jobs(self.mock_self)
        self.assertEqual(self.mock_self.index, 12)

    def test_prev_jobs(self):

        self.mock_self.count = 9
        BatchAppsHistory.show_prev_jobs(self.mock_self)
        self.assertEqual(self.mock_self.index, 0)

        self.mock_self.index = 4
        BatchAppsHistory.show_prev_jobs(self.mock_self)
        self.assertEqual(self.mock_self.index, 0)

        self.mock_self.index = 8
        BatchAppsHistory.show_prev_jobs(self.mock_self)
        self.assertEqual(self.mock_self.index, 3)

    def test_first_jobs(self):

        BatchAppsHistory.show_first_jobs(self.mock_self)
        self.assertEqual(self.mock_self.index, 0)

        self.mock_self.index = 8
        BatchAppsHistory.show_first_jobs(self.mock_self)
        self.assertEqual(self.mock_self.index, 0)

    def test_last_jobs(self):

        self.mock_self.count = 11
        BatchAppsHistory.show_last_jobs(self.mock_self)
        self.assertEqual(self.mock_self.index, 10)

        self.mock_self.count = 15
        BatchAppsHistory.show_last_jobs(self.mock_self)
        self.assertEqual(self.mock_self.index, 10)

    def test_job_selected(self):

        ui_job = mock.create_autospec(BatchAppsJobInfo)
        ui_job.index = 0

        self.mock_self.selected_job = None
        BatchAppsHistory.job_selected(self.mock_self, None)

        BatchAppsHistory.job_selected(self.mock_self, ui_job)
        self.assertEqual(self.mock_self.selected_job, ui_job)
        self.mock_self.update_job.assert_called_with(0)

        BatchAppsHistory.job_selected(self.mock_self, ui_job)
        ui_job.collapse.assert_called_with()
        
        self.mock_self.selected_job = None
        self.mock_self.jobs = []
        BatchAppsHistory.job_selected(self.mock_self, ui_job)
        ui_job.collapse.assert_called_with()

    @mock.patch("history.maya")
    def test_update_job(self, mock_maya):

        job = mock.create_autospec(SubmittedJob)
        job.status = "Running"
        job.percentage = "10%"
        job.time_submitted = "today"
        job.number_tasks = "500"
        job.id = "12345"
        job.pool_id = "67890"
        job.name = "Test Job"
        self.mock_self.jobs = [job]

        ui_job = mock.create_autospec(BatchAppsJobInfo)
        ui_job.index = 0
        self.mock_self.selected_job = ui_job

        def call(func):
            self.assertTrue(hasattr(func, '__call__'))

        self.mock_self._call = call

        BatchAppsHistory.update_job(self.mock_self, 0)
        ui_job.set_thumbnail.assert_called_with(os.path.join(
            os.environ["BATCHAPPS_ICONS"], "loading_preview.png"), 24)
        ui_job.set_status.assert_called_with("Running")

    def test_get_thumb(self):

        job = mock.create_autospec(SubmittedJob)
        job.status = "Running"
        job.get_tasks.return_value = [1,2,3]
        self.mock_self.jobs = [job]

        ui_job = mock.create_autospec(BatchAppsJobInfo)
        ui_job.index = 0

        def call(func):
            self.assertTrue(hasattr(func, '__call__'))
            return func()

        self.mock_self._call = call
        self.mock_self.selected_job = ui_job

        BatchAppsHistory.get_thumb(self.mock_self)
        self.mock_self.get_task_thumb.assert_called_with(job, [1,2,3])

        job.status = "Complete"
        BatchAppsHistory.get_thumb(self.mock_self)
        self.mock_self.get_job_thumb.assert_called_with(job)

        self.mock_self.jobs = []
        BatchAppsHistory.get_thumb(self.mock_self)
        ui_job.set_thumbnail.assert_called_with(os.path.join(os.environ["BATCHAPPS_ICONS"], "no_preview.png"), 24)

        self.mock_self.selected_job = None
        BatchAppsHistory.get_thumb(self.mock_self)

    @mock.patch("history.glob")
    @mock.patch("history.maya")
    def test_task_thumb(self, mock_maya, mock_glob):

        star = os.path.join(os.path.dirname(__file__), "data", "star.png")
        mock_glob.glob.return_value = []
        job = mock.create_autospec(SubmittedJob)
        job.id = "12345"

        task1 = mock.create_autospec(Task)
        task1.id = "abc"
        task1.get_thumbnail.side_effect = FileDownloadException("Broken!")

        task2 = mock.create_autospec(Task)
        task2.id = "abc"
        task2.get_thumbnail.return_value = star

        def call(func, dir, thumb, over):
            self.assertTrue(hasattr(func, '__call__'))
            self.assertTrue(over)
            self.assertTrue(thumb.startswith("12345.abc"))
            return func()

        self.mock_self.temp_name = lambda a: BatchAppsHistory.temp_name(self.mock_self, a)
        self.mock_self._call = call
        self.mock_self.selected_job = mock.create_autospec(BatchAppsJobInfo)
        BatchAppsHistory.get_task_thumb(self.mock_self, job, [task2, task1])
        self.mock_self.selected_job.set_thumbnail.assert_called_with(star, mock.ANY)
        mock_glob.glob.assert_called_with(mock.ANY)
        self.assertEqual(task2.get_thumbnail.call_count, 1)
        task2.get_thumbnail.call_count = 0

        mock_glob.glob.return_value = [star]
        BatchAppsHistory.get_task_thumb(self.mock_self, job, [task2, task1])
        self.assertEqual(task2.get_thumbnail.call_count, 0)

        mock_glob.glob.return_value = []
        task2.get_thumbnail.side_effect = FileDownloadException("Broken!")
        BatchAppsHistory.get_task_thumb(self.mock_self, job, [task2, task1])
        self.mock_self.selected_job.set_thumbnail.assert_called_with(
            os.path.join(os.environ["BATCHAPPS_ICONS"], "no_preview.png"), mock.ANY)

    @mock.patch("history.glob")
    @mock.patch("history.maya")
    def test_job_thumb(self, mock_maya, mock_glob):

        star = os.path.join(os.path.dirname(__file__), "data", "star.png")
        mock_glob.glob.return_value = []
        job = mock.create_autospec(SubmittedJob)
        job.id = "12345"
        job.get_thumbnail.side_effect = FileDownloadException("Broken!")

        def call(func, dir, thumb, over):
            self.assertTrue(hasattr(func, '__call__'))
            self.assertTrue(over)
            self.assertTrue(thumb.startswith("12345.job."))
            return func()

        self.mock_self.temp_name = lambda a: BatchAppsHistory.temp_name(self.mock_self, a)
        self.mock_self._call = call
        self.mock_self.selected_job = mock.create_autospec(BatchAppsJobInfo)
        BatchAppsHistory.get_job_thumb(self.mock_self, job)
        self.mock_self.selected_job.set_thumbnail.assert_called_with(
            os.path.join(os.environ["BATCHAPPS_ICONS"], "no_preview.png"), mock.ANY)
        job.get_thumbnail.call_count = 0

        mock_glob.glob.return_value = [star]
        BatchAppsHistory.get_job_thumb(self.mock_self, job)
        self.mock_self.selected_job.set_thumbnail.assert_called_with(star, mock.ANY)
        self.assertEqual(job.get_thumbnail.call_count, 0)

        mock_glob.glob.return_value = []
        job.get_thumbnail.side_effect = None
        job.get_thumbnail.return_value = star
        BatchAppsHistory.get_job_thumb(self.mock_self, job)
        self.mock_self.selected_job.set_thumbnail.assert_called_with(star, mock.ANY)
        self.assertEqual(job.get_thumbnail.call_count, 1)

    def test_cancel_job(self):

        job = mock.create_autospec(SubmittedJob)
        job.cancel.return_value = True

        def call(func):
            self.assertTrue(hasattr(func, '__call__'))
            return func()

        self.mock_self.jobs = [job]
        self.mock_self._call = call
        self.mock_self.selected_job = mock.create_autospec(BatchAppsJobInfo)
        self.mock_self.selected_job.index = 0

        BatchAppsHistory.cancel_job(self.mock_self)
        job.cancel.assert_called_with()
        job.cancel.call_count = 0

        self.mock_self.jobs = []
        BatchAppsHistory.cancel_job(self.mock_self)
        self.assertEqual(job.cancel.call_count, 0)

    @mock.patch("history.os")
    @mock.patch("history.tempfile")
    @mock.patch("history.shutil")
    @mock.patch("history.maya")
    def test_download_output(self, mock_maya, mock_util, mock_temp, mock_os):

        data_dir = os.path.join(os.path.dirname(__file__), "data")
        mock_temp.mkdtemp.return_value = data_dir
        mock_os.path.exists.return_value = False

        selected_file = os.path.join(os.path.dirname(__file__), "my_output.zip")
        job = mock.create_autospec(SubmittedJob)

        def call(func, dir, overwrite):
            self.assertTrue(hasattr(func, '__call__'))
            self.assertEqual(dir, data_dir)
            self.assertTrue(overwrite)
            func(dir, overwrite)
            return os.path.join(data_dir, "output.zip")

        self.mock_self.ui = mock.create_autospec(HistoryUI)
        self.mock_self.ui.refresh_button = mock.create_autospec(ProcButton)
        self.mock_self.jobs = [job]
        self.mock_self._call = call
        self.mock_self.selected_job = mock.create_autospec(BatchAppsJobInfo)
        self.mock_self.selected_job.index = 0

        BatchAppsHistory.download_output(self.mock_self, selected_file)
        job.get_output.assert_called_with(data_dir, overwrite=True, callback=mock.ANY, block=100000)

        job.get_output.side_effect = FileDownloadException("Failed!")
        BatchAppsHistory.download_output(self.mock_self, selected_file)
        self.mock_self.ui.refresh_button.finish.assert_called_with()

        job.get_output.call_count = 0
        job.get_output.side_effect = None
        mock_os.path.exists.return_value = True

        BatchAppsHistory.download_output(self.mock_self, selected_file)
        mock_os.remove.assert_called_with(selected_file)
        mock_util.move_assert_called_with(os.path.join(data_dir, "output.zip"), selected_file)
        mock_util.rmtree.assert_called_with(data_dir)

        mock_os.remove.side_effect = EnvironmentError("Couldn't delete...")
        BatchAppsHistory.download_output(self.mock_self, selected_file)
        self.mock_self.ui.refresh_button.finish.assert_called_with()
        self.assertEqual(job.get_output.call_count, 1)

        mock_util.rmtree.side_effect = Exception("Couldn't move to new location")
        BatchAppsHistory.download_output(self.mock_self, selected_file)
        self.mock_self.ui.refresh_button.finish.assert_called_with()
        mock_util.rmtree.assert_called_with(data_dir)

    def test_image_height(self):

        image = os.path.join(os.path.dirname(__file__), "data", "star.png")
        height = BatchAppsHistory.get_image_height(self.mock_self, image)
        self.assertEqual(height, 405)


class TestHistoryCombined(unittest.TestCase):

    @mock.patch("ui_history.utils")
    @mock.patch("ui_history.maya")
    @mock.patch("history.maya")
    def test_history(self, *args):

        def add_tab(tab):
            self.assertFalse(tab.ready)

        def call(func, *args, **kwargs):
            self.assertTrue(hasattr(func, '__call__'))
            return func(*args, **kwargs)

        layout = mock.Mock(add_tab=add_tab)
        history = BatchAppsHistory(layout, call)

        creds = mock.create_autospec(Credentials)
        conf = mock.create_autospec(Configuration)
        session = mock.Mock(credentials=creds, config=conf)

        history.configure(session)

        history.manager = mock.create_autospec(JobManager)
        job1 = mock.create_autospec(SubmittedJob)
        job1.name = "Job1"
        job1.status = "Complete"
        job1.percentage = "100%"
        job1.time_submitted = str(datetime.datetime.now()).replace(' ', 'T')
        job1.number_tasks = "10"
        job1.id = "12345"
        job1.pool_id = "pool"

        job2 = mock.create_autospec(SubmittedJob)
        job2.name = "Job2"

        history.manager.get_jobs.return_value = [job1, job2]
        history.manager.__len__.return_value = 2

        history.ui.prepare()
        self.assertTrue(history.ui.ready)
        self.assertTrue(history.min)
        self.assertTrue(history.max)

        history.ui.show_next_jobs()
        self.assertEqual(history.index, 2)
        self.assertFalse(history.min)
        self.assertTrue(history.max)

        history.ui.show_last_jobs()
        self.assertEqual(history.index, 0)
        self.assertTrue(history.min)
        self.assertTrue(history.max)

        history.ui.show_prev_jobs()
        self.assertEqual(history.index, 0)
        self.assertTrue(history.min)
        self.assertTrue(history.max)

        history.ui.show_first_jobs()
        self.assertEqual(history.index, 0)
        self.assertTrue(history.min)
        self.assertTrue(history.max)

        history.ui.jobs_displayed[0].on_expand()
        self.assertEqual(history.ui.jobs_displayed[0], history.selected_job)

        history.selected_job.collapse()
        self.assertIsNone(history.selected_job)

        history.ui.jobs_displayed[1].on_expand()
        self.assertIsNone(history.selected_job)

        mock_maya = args[1]
        mock_maya.file_select.return_value = os.path.join(os.path.dirname(__file__), "data", "my_output.zip")
        history.ui.jobs_displayed[0].download_output()
        self.assertEqual(job1.get_output.call_count, 0)

        history.ui.jobs_displayed[0].on_expand()
        history.ui.jobs_displayed[0].download_output()
        self.assertEqual(job1.get_output.call_count, 1)
