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
import json

try:
    import unittest2 as unittest
except ImportError:
    import unittest

try:
    from unittest import mock
except ImportError:
    import mock

from ui_environment import EnvironmentUI
from environment import BatchAppsEnvironment, BatchPlugin


class TestPlugin(unittest.TestCase):

    def setUp(self):
        self.mock_self = mock.create_autospec(BatchPlugin)
        return super(TestPlugin, self).setUp()

    @mock.patch.object(BatchPlugin, "create_checkbox")
    def test_create(self, mock_checkbox):
        
        plugin = BatchPlugin("base", "plugin", "False", [])
        mock_checkbox.assert_called_with()

        with self.assertRaises(AttributeError):
            v = plugin.license_var

        self.assertEqual(plugin.label, "plugin")
        self.assertFalse(plugin.license)
        self.assertFalse(plugin.supported)

        plugin = BatchPlugin("base", "plugin", "False", [{"name":"My Plugin", "license":False}])
        self.assertEqual(plugin.label, "My Plugin")
        self.assertFalse(plugin.license)
        self.assertTrue(plugin.supported)
        self.assertEqual(plugin.license_var, {})

    @mock.patch("environment.maya")
    def test_create_checkbox(self, mock_maya):
        self.mock_self.license = False
        self.mock_self.base = mock.create_autospec(BatchAppsEnvironment)
        self.mock_self.base.ui = mock.create_autospec(EnvironmentUI)
        self.mock_self.base.ui.plugin_layout = "layout"
        self.mock_self.supported = False
        self.mock_self.label = "plugin"
        self.mock_self.contents = []

        BatchPlugin.create_checkbox(self.mock_self)
        self.assertEqual(len(self.mock_self.contents), 2)
        mock_maya.check_box.assert_called_with(label="Unsupported: plugin", value=False, onCommand=self.mock_self.include,
                                               offCommand=self.mock_self.exclude, parent="layout", enable=False)
        mock_maya.text.assert_called_with(label="", parent="layout")

        self.mock_self.license = True
        self.mock_self.contents = []
        BatchPlugin.create_checkbox(self.mock_self)
        self.assertEqual(len(self.mock_self.contents), 4)

    @mock.patch("environment.maya")
    def test_is_used(self, mock_maya):
        
        used = ["plugin_A", "plugin_B"]
        self.mock_self.base = mock.create_autospec(BatchAppsEnvironment)
        self.mock_self.base.plugins = []
        self.mock_self.base.warnings = []
        self.mock_self.plugin = "plugin_C.py"
        self.mock_self.label = "plugin"
        self.mock_self.supported = False
        self.mock_self.loaded = False
        self.mock_self.license = False
        self.mock_self.checkbox = "checkbox"
        self.mock_self.license_check = "license"
        BatchPlugin.is_used(self.mock_self, used)
        self.assertFalse(self.mock_self.used)
        self.assertEqual(self.mock_self.base.plugins, [])
        self.assertEqual(self.mock_self.base.warnings, [])

        self.mock_self.loaded = True
        BatchPlugin.is_used(self.mock_self, used)
        self.assertFalse(self.mock_self.used)
        self.assertEqual(self.mock_self.base.plugins, [])
        self.assertEqual(self.mock_self.base.warnings, [])

        self.mock_self.plugin = "plugin_A.py"
        BatchPlugin.is_used(self.mock_self, used)
        self.assertTrue(self.mock_self.used)
        self.assertEqual(mock_maya.check_box.call_count, 0)
        self.assertEqual(self.mock_self.base.plugins, [])
        self.assertEqual(self.mock_self.base.warnings, ["plugin_A.py"])

        self.mock_self.supported = True
        self.mock_self.base.warnings = []
        BatchPlugin.is_used(self.mock_self, used)
        self.assertTrue(self.mock_self.used)
        mock_maya.check_box.assert_called_with("checkbox", edit=True, value=True)
        self.assertEqual(self.mock_self.base.plugins, ["plugin"])
        self.assertEqual(self.mock_self.base.warnings, [])

        self.mock_self.license = True
        BatchPlugin.is_used(self.mock_self, used)
        mock_maya.check_box.assert_called_with("license", edit=True, enable=True)

    @mock.patch("environment.maya")
    def test_use_license(self, mock_maya):
        
        self.mock_self.license = False
        self.mock_self.custom_license_endp = "endp"
        self.mock_self.custom_license_port = "port"
        BatchPlugin.use_license(self.mock_self, True)
        self.assertEqual(mock_maya.text_field.call_count, 0)

        self.mock_self.license = True
        BatchPlugin.use_license(self.mock_self, True)
        self.assertEqual(mock_maya.text_field.call_count, 2)
        mock_maya.text_field.assert_called_with("port", edit=True, enable=True)

    @mock.patch("environment.maya")
    def test_include(self, mock_maya):
        
        self.mock_self.base = mock.create_autospec(BatchAppsEnvironment)
        self.mock_self.base.plugins = []
        self.mock_self.label = "My Plugin"
        self.mock_self.license = False
        self.mock_self.license_check = "check"
        BatchPlugin.include(self.mock_self)
        self.assertEqual(self.mock_self.base.plugins, ["My Plugin"])
        self.assertEqual(mock_maya.check_box.call_count, 0)

        self.mock_self.license = True
        BatchPlugin.include(self.mock_self)
        self.assertEqual(self.mock_self.base.plugins, ["My Plugin", "My Plugin"])
        mock_maya.check_box.assert_called_with("check", edit=True, enable=True)

    @mock.patch("environment.maya")
    def test_exclude(self, mock_maya):

        self.mock_self.base = mock.create_autospec(BatchAppsEnvironment)
        self.mock_self.base.plugins = ["My Plugin"]
        self.mock_self.label = "My Plugin"
        self.mock_self.license = False
        self.mock_self.license_check = "check"
        self.mock_self.used = False

        BatchPlugin.exclude(self.mock_self)
        self.assertEqual(mock_maya.warning.call_count, 0)
        self.assertEqual(mock_maya.check_box.call_count, 0)
        self.assertEqual(self.mock_self.base.plugins, [])

        self.mock_self.license = True
        BatchPlugin.exclude(self.mock_self)
        self.assertEqual(mock_maya.warning.call_count, 0)
        mock_maya.check_box.assert_called_with("check", edit=True, enable=False)
        self.assertEqual(self.mock_self.base.plugins, [])

        self.mock_self.used = True
        BatchPlugin.exclude(self.mock_self)
        mock_maya.warning.assert_called_with(mock.ANY)

    @mock.patch("environment.maya")
    def test_delete(self, mock_maya):

        self.mock_self.contents = ["a"]
        BatchPlugin.delete(self.mock_self)
        mock_maya.delete_ui.assert_called_with("a", control=True)

    @mock.patch("environment.maya")
    def test_get_vaiables(self, mock_maya):
        
        mock_maya.check_box.return_value = True
        self.mock_self.license = False
        self.mock_self.license_check = "check"
        self.mock_self.license_var = {"key":"solidangle_LICENSE", "value":"{port}@{host}"}
        self.mock_self.custom_license_endp = "host"
        self.mock_self.custom_license_port = "port"
        vars = BatchPlugin.get_variables(self.mock_self)
        self.assertEqual(vars, {})
        self.assertEqual(mock_maya.text_field.call_count, 0)

        self.mock_self.license = True
        mock_maya.text_field.return_value = "blah"
        vars = BatchPlugin.get_variables(self.mock_self)
        self.assertEqual(vars, {"solidangle_LICENSE":"blah@blah"})
        self.assertEqual(mock_maya.text_field.call_count, 2)


class TestBatchAppsEnvironment(unittest.TestCase):

    def setUp(self):
        self.mock_self = mock.create_autospec(BatchAppsEnvironment)
        self.mock_self._log = logging.getLogger("TestEnvironment")
        self.mock_self._server_plugins = []
        self.mock_self.warnings = []
        self.mock_self._plugins = []
        self.mock_self._version = "2017"
        return super(TestBatchAppsEnvironment, self).setUp()

    @mock.patch.object(BatchAppsEnvironment, "refresh")
    @mock.patch("environment.EnvironmentUI")
    @mock.patch("environment.callback")
    def test_create(self, mock_call, mock_ui, mock_refresh):

        env = BatchAppsEnvironment("frame", "call")
        mock_ui.assert_called_with(env, "frame", ["Maya I/O PR55"])
        mock_call.after_new.assert_called_with(mock.ANY)
        mock_call.after_read.assert_called_with(mock.ANY)
        mock_refresh.assert_called_with()

        self.assertEqual(env.plugins, [])
        self.assertEqual(env.version, "2017")
        lic = env.license
        env.ui.get_license_server.assert_called_with()
        vars = env.environment_variables
        env.ui.get_env_vars.assert_called_with()

    def test_configure(self):
        
        BatchAppsEnvironment.configure(self.mock_self, "session")
        self.assertEqual(self.mock_self._session, "session")

    @mock.patch("environment.BatchPlugin")
    @mock.patch("environment.maya")
    def test_get_plugins(self, mock_maya, mock_plugin):
        
        mock_maya.plugins.return_value = ["mtoa.mll", "b", "c"]
        self.mock_self.search_for_plugins.return_value = ["Mayatomr.mll", "mtoa.mll", "c", "d", "e"]
        mock_plugin.return_value = mock.create_autospec(BatchPlugin)
        plugins = BatchAppsEnvironment.get_plugins(self.mock_self)

        mock_maya.plugins.assert_any_call('e', query=True, loaded=True)
        self.mock_self.search_for_plugins.assert_called_with()

        mock_plugin.assert_any_call(mock.ANY, "mtoa.mll", ["mtoa.mll", "b", "c"],
                                    [{"name": "Arnold", "plugin": "mtoa.", "license": True, "license_var": {"key":"solidangle_LICENSE", "value":"{port}@{host}"}}])
        mock_plugin.assert_any_call(mock.ANY, "e", ["mtoa.mll", "b", "c"], [])
        mock_plugin.assert_any_call(mock.ANY, "Mayatomr.mll", ["mtoa.mll", "b", "c"],
                                    [{"name": "MentalRay", "plugin": "Mayatomr.", "license": False}])
        mock_plugin.return_value.is_used.assert_called_with(["mtoa.mll", "b", "c"])
        self.assertEqual(len(plugins), 5)

        self.mock_self.warnings = ["a","b","c"]
        plugins = BatchAppsEnvironment.get_plugins(self.mock_self)
        mock_maya.warning.assert_called_with("The following plug-ins are used in the scene, but not yet supported.\nRendering may be affected.\na\nb\nc\n")

    @mock.patch("environment.os")
    def test_search_for_plugins(self, mock_os):

        self.mock_self.is_default = lambda a: BatchAppsEnvironment.is_default(self.mock_self, a)
        mock_os.path.splitext = os.path.splitext
        mock_os.environ = {"MAYA_PLUG_IN_PATH":"dir1;dir2;dir3"}
        mock_os.pathsep = ';'
        mock_os.path.isdir.return_value = True
        mock_os.listdir.return_value = ["a","b","test.mll","test.mll","plugin.py", "xgenMR.py", "fbxmaya.mll"]
        plugins = BatchAppsEnvironment.search_for_plugins(self.mock_self)
        self.assertEqual(sorted(plugins), sorted(["test.mll", "plugin.py"]))
        
    def test_set_version(self):

        BatchAppsEnvironment.set_version(self.mock_self, "Maya 2015")
        self.assertEqual(self.mock_self._version, "2017")
        BatchAppsEnvironment.set_version(self.mock_self, "test")
        self.assertEqual(self.mock_self._version, "2017")

    def test_refresh(self):
        self.mock_self._server_plugins = [1,2,3]
        self.mock_self.warnings = [4,5,6]
        mock_plugin = mock.create_autospec(BatchPlugin)
        self.mock_self._plugins = [mock_plugin]

        BatchAppsEnvironment.refresh(self.mock_self)
        self.assertEqual(self.mock_self._server_plugins, [])
        self.assertEqual(self.mock_self.warnings, [])
        self.mock_self.get_plugins.assert_called_with()
        mock_plugin.delete.assert_called_with()


class TestEnvironmentCombined(unittest.TestCase):

    @mock.patch("ui_environment.utils")
    @mock.patch("ui_environment.maya")
    @mock.patch("environment.callback")
    @mock.patch("environment.maya")
    def test_environment(self, *args):

        os.environ["MAYA_PLUG_IN_PATH"] = os.path.join(os.path.dirname(__file__), "data", "modules")

        def add_tab(tab):
            self.assertFalse(tab.ready)

        def call(func, *args, **kwargs):
            self.assertTrue(hasattr(func, '__call__'))
            return func(*args, **kwargs)

        layout = mock.Mock(add_tab=add_tab)
        env = BatchAppsEnvironment(layout, call)

        env.configure("session")
        self.assertEqual(env.plugins, [])


if __name__ == '__main__':
    unittest.main()