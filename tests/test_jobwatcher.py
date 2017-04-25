try:
    import unittest2 as unittest
except ImportError:
    import unittest

try:
   from unittest import mock
except ImportError:
   import mock

import os, sys

from batchapps import (
    JobManager,
    Configuration)

from batchapps.job import (
    SubmittedJob,
    Task,
    JobSubmission)

from batchapps.exceptions import (
    RestCallException,
    AuthenticationException,
    InvalidConfigException)

with mock.patch.object(sys, "argv"):
    import job_watcher as client

class TestJobWatcher(unittest.TestCase):

    def setUp(self):
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        return super(TestJobWatcher, self).setUp()

    def test_check_valid_dir(self):
        
        with self.assertRaises(RuntimeError):
            client._check_valid_dir(None)

        with self.assertRaises(RuntimeError):
            client._check_valid_dir("test")

        with self.assertRaises(RuntimeError):
            client._check_valid_dir(1)

        self.assertEqual(client._check_valid_dir(self.cwd), self.cwd)

    @mock.patch.object(client, "_check_valid_dir")
    @mock.patch('job_watcher.os')
    def test_download_tasks_outputs(self, mock_os, mock_check_valid_dir):

        client._download_task_outputs(None, [], None)
        self.assertFalse(mock_os.path.join.called, "Output list is empty")

        mock_task = mock.create_autospec(Task)
        mock_outputs = [{'type': 'TaskOutput', 'name': 'test.png'}]
        mock_check_valid_dir.return_value = "test_dir"
        mock_os.path.isfile.return_value = False

        client._download_task_outputs(mock_task, mock_outputs, "test_dir")
        mock_os.path.join.assert_called_with("test_dir", "test.png")
        mock_task.get_output.assert_called_with({'type': 'TaskOutput', 'name': 'test.png'}, "test_dir",
                                                callback=mock.ANY, block=100000)

    @mock.patch.object(client, '_download_task_outputs')
    def test_track_completed_tasks(self, mock_download_task_outputs):

        mock_job = mock.create_autospec(SubmittedJob)

        mock_job.get_tasks.side_effect = RestCallException("RestCallException", "RestCallExceptionRaised", None)

        with self.assertRaises(RuntimeError):
            client._track_completed_tasks(mock_job, "test_dir")

        mock_job.get_tasks.side_effect = None
        mock_job.get_tasks.return_value = [1, 2, 3]

        with self.assertRaises(RuntimeError):
            client._track_completed_tasks(mock_job, "test_dir")

        mock_task1 = mock.create_autospec(Task)
        mock_task1.status = "Complete"
        mock_task1.id = 1
        mock_task1.outputs = []
        mock_task2 = mock.create_autospec(Task)
        mock_task2.status = "Complete"
        mock_task2.id = 2
        mock_task2.outputs = []

        mock_job.number_tasks = 3

        mock_job.get_tasks.return_value = [mock_task1, mock_task2]

        client._track_completed_tasks(mock_job, "test_dir")

    def test_retrieve_logs(self):

        mock_job = mock.create_autospec(SubmittedJob)

        client._retrieve_logs(mock_job)

        mock_job.get_logs.side_effect = RestCallException("RestCallException", "RestCalleExceptionRaised", None)

        with self.assertRaises(RuntimeError):
            client._retrieve_logs(mock_job)

        mock_job.get_logs.side_effect = None
        mock_job.get_logs.return_value = {}

        self.assertIsNone(client._retrieve_logs(mock_job))
        
        mock_job.get_logs.return_value = {'upTo': None}

        with self.assertRaises(RuntimeError):
            client._retrieve_logs(mock_job)

        mock_job.get_logs.return_value = {'upTo': None,
                                          'messages': [{'timestamp': '1800-09-23bla',
                                                        'text': 'This is a test message',
                                                        'taskId': 2}]}
        self.assertTrue(mock_job.get_logs()['messages'])

    @mock.patch.object(client, "_retrieve_logs")
    def test_check_job_stopped(self, mock_retrieve_logs):

        mock_job = mock.create_autospec(SubmittedJob)

        with self.assertRaises(RuntimeError):
            client._check_job_stopped(mock_job)

        mock_job.status = "test"
        client._check_job_stopped(mock_job)

        mock_job.status = "Error"
        with self.assertRaises(RuntimeError):
            client._check_job_stopped(mock_job)
        self.assertTrue(mock_retrieve_logs.called)

        mock_job.status = "OnHold"
        with self.assertRaises(RuntimeError):
            client._check_job_stopped(mock_job)

        mock_job.status = "Complete"
        self.assertTrue(client._check_job_stopped(mock_job))

        mock_job.status = "NotStarted"
        self.assertFalse(client._check_job_stopped(mock_job))

        mock_job.status = "InProgress"
        self.assertFalse(client._check_job_stopped(mock_job))

    @mock.patch.object(client, "_check_job_stopped")
    @mock.patch.object(client, "_track_completed_tasks")
    def test_track_job_progress(self, mock_track_completed_tasks, mock_check_job_stopped):
        
        mock_job_manager = mock.create_autospec(JobManager)
        mock_id = "test_id"
        mock_dwnld_dir = "test_dir"
        mock_job = mock.create_autospec(SubmittedJob)
        mock_job.status = "test"
        mock_job_manager.get_job.return_value = mock_job

        with self.assertRaises(RuntimeError):
            client.track_job_progress(mock_job_manager, mock_id, mock_dwnld_dir)

        mock_job.status = "Error"
        mock_job.percentage = "30"
        mock_check_job_stopped.side_effect = RuntimeError("RuntimeError", "RuntimeError raised", None)
        with self.assertRaises(RuntimeError):
            client.track_job_progress(mock_job_manager, mock_id, mock_dwnld_dir)

        mock_job.status = "InProgress"
        mock_check_job_stopped.side_effect = [False, True]
        self.assertFalse(client.track_job_progress(mock_job_manager, mock_id, mock_dwnld_dir))
        self.assertEqual(mock_job.update.call_count, 1)

        mock_job.status = "Complete"
        mock_check_job_stopped.side_effect = None
        self.assertIsNone(client.track_job_progress(mock_job_manager, mock_id, mock_dwnld_dir), "track_job_progress returned None unexpectedly.")

    @mock.patch("job_watcher.webbrowser")
    @mock.patch("job_watcher.AzureOAuth")
    def test_authentication(self, mock_azureoauth, mock_webbrowser):

        
        mock_azureoauth.get_unattended_session.return_value = "Auth"
        auth = client.authentication("test")
        self.assertEqual("Auth", auth)
        self.assertFalse(mock_azureoauth.get_session.called)

        mock_azureoauth.get_unattended_session.side_effect = InvalidConfigException("InvalidConfigException", "InvalidConfigException raised", None)
        
        client.authentication("test")
        self.assertTrue(mock_azureoauth.get_session.called)

        mock_azureoauth.get_session.return_value = "Done!"
        auth = client.authentication("test")
        self.assertEqual("Done!", auth)
        mock_azureoauth.get_session.called_with(config="test")

        mock_azureoauth.get_session.side_effect = InvalidConfigException("InvalidConfigException", "InvalidConfigException raised", None)

        with self.assertRaises(RuntimeError):
            client.authentication("test")

        mock_azureoauth.get_authorization_token.side_effect = InvalidConfigException("InvalidConfigException", "InvalidConfigExceptio Raised", None)

        with self.assertRaises(RuntimeError):
            client.authentication("test")

        mock_azureoauth.get_session.side_effect = AuthenticationException("AuthenticationException", "AuthenticationException raised", None)

    @mock.patch("job_watcher.Configuration")
    def test_generate_config(self, mock_cfg):

        mock_data_path = "test"
        with self.assertRaises(EnvironmentError):
            client.generate_config(mock_data_path)

        mock_cfg.side_effect = InvalidConfigException("InvalidConfigException", "InvalidConfigException Raised", None)
        
        mock_data_path = os.path.dirname(os.path.normpath(__file__))
        with self.assertRaises(ValueError):
            client.generate_config(mock_data_path)

        mock_cfg.side_effect = None
        self.assertEqual(client.generate_config(mock_data_path), mock_cfg())
        

