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

from ui_shared import BatchAppsUI
from shared import BatchAppsSettings


class TestBatchAppsShared(unittest.TestCase):

    def setUp(self):
        self.mock_self = mock.create_autospec(BatchAppsSettings)
        self.mock_self._log = logging.getLogger("TestShared")

        return super(TestBatchAppsShared, self).setUp()

    #@mock.patch("shared.maya")
    #def test_check_version(self, mock_maya):

    #    self.mock_self.supported_versions = [2015]
    #    mock_maya.mel.return_value = 2015
    #    self.mock_self.check_version = lambda a: BatchAppsSettings.check_version(self.mock_self, a)

    #    ver = BatchAppsSettings.check_maya_version(self.mock_self)
    #    self.assertEqual(ver, 2015)
    #    self.assertFalse(mock_maya.warning.call_count)

    #    mock_maya.mel.return_value = 2016
    #    ver = BatchAppsSettings.check_maya_version(self.mock_self)
    #    self.assertEqual(ver, 2015)
    #    self.assertTrue(mock_maya.warning.call_count)

    #    mock_maya.mel.return_value = 2014
    #    ver = BatchAppsSettings.check_maya_version(self.mock_self)
    #    self.assertEqual(ver, 2015)
    #    self.assertEqual(mock_maya.warning.call_count, 2)

