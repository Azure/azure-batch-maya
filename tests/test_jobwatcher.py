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
from azure.batch_extensions import models

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

    @mock.patch.object(client, 'batch_client')
    def test_watcher_track_completed_outputs(self,  mock_batchClient):
        blob = namedtuple("Blob", "name, properties")

        mock_batchClient.file.list_from_group.return_value = ({
            'name': b.name,
            'size': b.properties.content_length}
            for b in  [
                blob("job_output.exr",  mock.Mock(content_length=1)),
                blob("subdir/job_output.png", mock.Mock(content_length=1)),
                blob("thumbs/0.png",  mock.Mock(content_length=1)),
                blob("logs/frame_0.log",  mock.Mock(content_length=1)),
                blob("logs/frame_0_error.log",  mock.Mock(content_length=1))])

        client._track_completed_outputs("container", "\\test_dir")

        self.assertEqual(mock_batchClient.file.download.call_count, 4)
        mock_batchClient.file.download.assert_any_call('\\test_dir', 'container', remote_path='job_output.exr')
        mock_batchClient.file.download.assert_any_call('\\test_dir', 'container', remote_path='subdir/job_output.png')
        mock_batchClient.file.download.assert_any_call('\\test_dir', 'container', remote_path='logs/frame_0.log')
        mock_batchClient.file.download.assert_any_call('\\test_dir', 'container', remote_path='logs/frame_0_error.log')

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
