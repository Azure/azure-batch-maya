# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

try:
    import unittest2 as unittest
except ImportError:
    import unittest

try:
   from unittest import mock
except ImportError:
   import mock

import os
import sys
from collections import namedtuple
from batch_extensions import models

CWD = os.path.dirname(os.path.abspath(__file__))
top_dir = os.path.dirname(CWD)
src_dir = os.path.join(top_dir, 'azure_batch_maya', 'scripts')
tools_dir = os.path.join(src_dir, 'tools')
sys.path.extend([src_dir, tools_dir])

with mock.patch.object(sys, "argv"):
    import job_watcher as client

class TestBlob(object):
    def __init__(self, name):
        self.name = name
        self.properties = object


class TestJobWatcher(unittest.TestCase):

    def test_watcher_check_valid_dir(self):
        with self.assertRaises(RuntimeError):
            client._check_valid_dir(None)
        with self.assertRaises(RuntimeError):
            client._check_valid_dir("//test")
        with self.assertRaises(RuntimeError):
            client._check_valid_dir(1)
        self.assertEqual(client._check_valid_dir(CWD), CWD)

    @mock.patch.object(client, 'storage_client')
    @mock.patch.object(client, '_download_output')
    def test_watcher_track_completed_outputs(self, mock_download, mock_storage):
        blob = namedtuple("Blob", "name, properties")
        mock_storage.list_blobs.return_value = [
            blob("job_output.exr",  mock.Mock(content_length=1)),
            blob("subdir/job_output.png", mock.Mock(content_length=1)),
            blob("thumbs/0.png",  mock.Mock(content_length=1)),
            blob("logs/frame_0.log",  mock.Mock(content_length=1)),
            blob("logs/frame_0_error.log",  mock.Mock(content_length=1))]

        client._track_completed_outputs("container", "\\test_dir")
        mock_storage.list_blobs.assert_called_with("container")
        self.assertEqual(mock_download.call_count, 4)
        mock_download.assert_any_call('container', 'job_output.exr', '\\test_dir\\job_output.exr', 1)
        mock_download.assert_any_call('container', 'subdir/job_output.png', '\\test_dir\\subdir\\job_output.png', 1)
        mock_download.assert_any_call('container', 'logs/frame_0.log', '\\test_dir\\logs\\frame_0.log', 1)
        mock_download.assert_any_call('container', 'logs/frame_0_error.log', '\\test_dir\\logs\\frame_0_error.log', 1)

    def test_watcher_check_job_stopped(self):
        mock_job = mock.create_autospec(models.CloudJob)
        with self.assertRaises(RuntimeError):
            client._check_job_stopped(mock_job)
        mock_job.state = "test"
        with self.assertRaises(RuntimeError):
            client._check_job_stopped(mock_job)

        mock_job.state = models.JobState.disabled
        with self.assertRaises(RuntimeError):
            client._check_job_stopped(mock_job)

        mock_job.state = models.JobState.completed
        self.assertTrue(client._check_job_stopped(mock_job))

        mock_job.state = models.JobState.active
        self.assertFalse(client._check_job_stopped(mock_job))
