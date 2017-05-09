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


if sys.version_info[:2] < (2, 7, ):
    try:
        import unittest2
        from unittest2 import TestLoader, TextTestRunner

    except ImportError:
        print("The Batch Maya Plugin test suite requires "
              "the unittest2 package to run on Python 2.6 and "
              "below.\nPlease install this package to continue.")
        sys.exit()
else:
    import unittest
    from unittest import TestLoader, TextTestRunner

if sys.version_info[:2] >= (3, 3, ):
    from unittest import mock
else:
    try:
        import mock
    except ImportError:
        print("The Batch Maya Plugin test suite requires "
              "the mock package to run on Python 3.2 and below.\n"
              "Please install this package to continue.")
        raise


if __name__ == '__main__':

    runner = TextTestRunner(verbosity=2)

    test_dir = os.path.dirname(__file__)
    top_dir = os.path.dirname(test_dir)
    src_dir = os.path.join(top_dir, 'azure_batch_maya', 'scripts')
    mod_dir = os.path.join(test_dir, 'data', 'modules')
    ui_dir = os.path.join(src_dir, 'ui')
    tools_dir = os.path.join(src_dir, 'tools')
    os.environ["AZUREBATCH_ICONS"] = os.path.join(top_dir, 'azure_batch_maya', 'icons')
    os.environ["AZUREBATCH_MODULES"] = mod_dir
    os.environ["AZUREBATCH_SCRIPTS"] = "{0};{1};{2}".format(src_dir, ui_dir, tools_dir)
    sys.path.extend([src_dir, ui_dir, tools_dir, mod_dir])

    test_loader = TestLoader()
    suite = test_loader.discover(test_dir,
                                 pattern="test_*.py",
                                 top_level_dir=top_dir)
    runner.run(suite)
