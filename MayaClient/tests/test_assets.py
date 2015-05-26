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

try:
    import unittest2 as unittest
except ImportError:
    import unittest

try:
    from unittest import mock
except ImportError:
    import mock

from ui_assets import AssetsUI
from assets import Asset, Assets, BatchAppsAssets
from batchapps import FileManager, Configuration, Credentials
from batchapps.files import UserFile, FileCollection

class TestAsset(unittest.TestCase):
    
    def setUp(self):
        self.mock_self = mock.create_autospec(Asset)
        self.mock_file = mock.create_autospec(UserFile)
        self.mock_file.path = "/my/test_path"
        return super(TestAsset, self).setUp()
    
    def test_create_asset(self):
        
        self.mock_file._exist = True
        self.mock_file.__bool__.return_value = True

        test_asset = Asset(self.mock_file, None)
        self.assertEqual(test_asset.label, "    test_path")
        self.assertEqual(test_asset.path, "/my/test_path")
        self.assertEqual(test_asset.note, "Can't find /my/test_path")

        self.mock_file.__bool__.return_value = True
        test_asset = Asset(self.mock_file, None)
        #self.assertEqual(test_asset.note, "/test_path")

    @mock.patch("assets.maya")
    def test_display(self, mock_api):

        self.mock_self.file = self.mock_file
        self.mock_self.label = "label"
        self.mock_self.note = "note"
        #self.mock_file.__bool__ = True
        
        Asset.display(self.mock_self, "layout")
        mock_api.check_box.assert_called_with(label="label",
                                              value=False,
                                              enable=False,
                                              parent="layout",
                                              onCommand=mock.ANY,
                                              offCommand=mock.ANY,
                                              annotation="note")

    @mock.patch("assets.maya")
    def test_included(self, mock_api):

        self.mock_self.file = self.mock_file
        self.mock_self.check_box = None

        val = Asset.included(self.mock_self)
        self.assertFalse(val)

        self.mock_self.check_box = 1
        val = Asset.included(self.mock_self)
        mock_api.check_box.assert_called_with(1, query=True, value=True)

    def test_include(self):

        self.mock_self.parent_list = []
        Asset.include(self.mock_self)
        self.assertEqual(self.mock_self.parent_list, [self.mock_self])

        Asset.include(self.mock_self)
        self.assertEqual(self.mock_self.parent_list, [self.mock_self])

    def test_exclude(self):

        self.mock_self.parent_list = []
        Asset.exclude(self.mock_self)
        self.assertEqual(self.mock_self.parent_list, [])

        self.mock_self.parent_list = ["test"]
        Asset.exclude(self.mock_self)
        self.assertEqual(self.mock_self.parent_list, ["test"])

        self.mock_self.parent_list = [self.mock_self]
        Asset.exclude(self.mock_self)
        self.assertEqual(self.mock_self.parent_list, [])

    @mock.patch("assets.maya")
    def test_delete(self, mock_api):

        self.mock_self.parent_list = []
        self.mock_self.check_box = 1

        Asset.delete(self.mock_self)
        mock_api.delete_ui.assert_called_with(1, control=True)
        self.assertEqual(self.mock_self.parent_list, [])

        self.mock_self.parent_list = [self.mock_self]
        Asset.delete(self.mock_self)
        mock_api.delete_ui.assert_called_with(1, control=True)
        self.assertEqual(self.mock_self.parent_list, [])

    def test_check(self):

        new_file = mock.create_autospec(UserFile)
        new_file.path = "C:\\TEST_file\\WeiRD_path"
        self.mock_self.path = "c:\\test_file\\Weird_path"

        check = Asset.check(self.mock_self, [new_file])
        self.assertTrue(check)

        new_file.path = "C:\\TEST_file\\WeiRD_path\\different"
        check = Asset.check(self.mock_self, [new_file])
        self.assertFalse(check)

class TestAssets(unittest.TestCase):

    def setUp(self):
        self.mock_self = mock.create_autospec(Assets)
        self.mock_self._log = logging.getLogger("TestAssets")
        return super(TestAssets, self).setUp()

    def test_create_assets(self):

        test_assets = Assets()
        self.assertIsNone(test_assets.manager)
        self.assertEqual(test_assets.refs, {'Additional':[]})

    def test_gather(self):

        self.mock_self.refs = {}
        self.mock_self.get_textures.return_value = {'a':1}
        self.mock_self.get_caches.return_value = {'b':2}
        self.mock_self.get_references.return_value = {'c':3}

        Assets.gather(self.mock_self, "manager")
        self.assertEqual(self.mock_self.refs, {'a':1, 'b':2, 'c':3})
        self.assertEqual(self.mock_self.manager, "manager")

        self.assertEqual(self.mock_self.get_textures.call_count, 1)
        self.assertEqual(self.mock_self.get_caches.call_count, 1)
        self.assertEqual(self.mock_self.get_references.call_count, 1)

    @mock.patch("assets.Asset")
    def test_extend(self, mock_asset):

        self.mock_self.pathmaps = []
        self.mock_self.refs = {}
        self.mock_self.manager = mock.create_autospec(FileManager)
        mock_asset.return_value = mock.create_autospec(Asset)
        mock_asset.return_value.check.return_value = True
        self.mock_self.manager.file_from_path.return_value = "UserFile"

        Assets.extend(self.mock_self, {"new_path":["/test_path/test_file"]})
        self.assertEqual(self.mock_self.pathmaps, ["/test_path"])
        mock_asset.assert_called_with("UserFile", [])
        self.assertEqual(self.mock_self.refs, {"new_path": []})

        mock_asset.return_value.check.return_value = False
        Assets.extend(self.mock_self, {"new_path":["/test_path/test_file"]})
        self.assertEqual(self.mock_self.refs, {"new_path": [mock.ANY]})

        mock_asset.side_effect = Exception("error!")
        Assets.extend(self.mock_self, {"new_path":["/test_path/test_file"]})
        self.assertEqual(self.mock_self.refs, {"new_path": []})

    def test_collect(self):

        self.mock_self.refs = {}
        files = Assets.collect(self.mock_self)
        self.assertEqual(files, [])

        test_file = mock.create_autospec(Asset)
        test_file.file = "my_test_file"
        self.mock_self.refs["Test1"] = [test_file]
        files = Assets.collect(self.mock_self)
        test_file.included.assert_called_once_with()
        self.assertEqual(files, ["my_test_file"])

    @mock.patch("assets.Asset")
    @mock.patch("assets.maya")
    def test_get_textures(self, mock_maya, mock_asset):

        self.mock_self.pathmaps = []
        self.mock_self.manager = mock.create_autospec(FileManager)
        mock_asset.return_value = mock.create_autospec(Asset)
        mock_asset.return_value.check.return_value = True
        self.mock_self.manager.file_from_path.return_value = "UserFile"

        class TestIter(object):

            def __init__(self):
                self.current = None
                self.itr = iter(range(0,5))

            def is_done(self):
                try:
                    self.current = self.itr.next()
                    return False
                except StopIteration:
                    return True

            def get_references(self):
                return ["dir1/1", "dir2/2", "dir3/3"]

        mock_maya.dependency_nodes.return_value = TestIter()
        tex = Assets.get_textures(self.mock_self)
        self.assertEqual(tex, {'Files': []})
        self.assertEqual(set(self.mock_self.pathmaps), set(["dir1", "dir2", "dir3"]))
        self.assertEqual(mock_asset.call_count, 15)
        mock_asset.assert_called_with("UserFile", [])

        mock_asset.return_value.check.return_value = False
        mock_maya.dependency_nodes.return_value = TestIter()
        tex = Assets.get_textures(self.mock_self)
        self.assertEqual(len(tex['Files']), 15)

    def test_get_references(self):

        refs = Assets.get_references(self.mock_self)
        self.assertEqual(refs, {})

    @mock.patch("assets.Asset")
    @mock.patch("assets.maya")
    def test_get_caches(self, mock_maya, mock_asset):

        self.mock_self.pathmaps = []
        self.mock_self.manager = mock.create_autospec(FileManager)
        mock_asset.return_value = mock.create_autospec(Asset)
        mock_maya.get_list.return_value = ["1", "2", "3"]
        mock_maya.get_attr.return_value = "/test_path/test_file"
        self.mock_self.manager.file_from_path.return_value = "UserFile"

        caches = Assets.get_caches(self.mock_self)
        self.assertEqual(caches, {'Caches': [mock.ANY, mock.ANY, mock.ANY]})
        self.assertEqual(set(self.mock_self.pathmaps), set(["/test_path"]))

    @mock.patch("assets.Asset")
    def test_add_asset(self, mock_asset):

        self.mock_self.pathmaps = []
        self.mock_self.refs = {'Additional':[]}
        self.mock_self.manager = mock.create_autospec(FileManager)
        mock_asset.return_value = mock.create_autospec(Asset)
        mock_asset.return_value.check.return_value = True
        self.mock_self.manager.file_from_path.return_value = "UserFile"

        Assets.add_asset(self.mock_self, "/test_path/my_asset", "layout")
        self.assertEqual(self.mock_self.pathmaps, ["/test_path"])
        self.assertEqual(self.mock_self.refs, {'Additional':[]})
        mock_asset.return_value.check.assert_called_once_with([])
        mock_asset.assert_called_once_with("UserFile", [])

        mock_asset.return_value.check.return_value = False
        Assets.add_asset(self.mock_self, "/test_path/my_asset", "layout")
        self.assertEqual(self.mock_self.refs, {'Additional':[mock.ANY]})
        mock_asset.return_value.display.assert_called_with("layout")

    def test_get_pathmaps(self):

        self.mock_self.pathmaps = []
        maps = Assets.get_pathmaps(self.mock_self)
        self.assertEqual(maps, '{"PathMaps": []}')

        self.mock_self.pathmaps = ["test", "", "test", None, 0, 5, "", "test"]
        maps = Assets.get_pathmaps(self.mock_self)
        self.assertEqual(maps, '{"PathMaps": ["test", "5"]}')


class TestBatchAppsAssets(unittest.TestCase):

    def setUp(self):
        self.mock_self = mock.create_autospec(BatchAppsAssets)
        self.mock_self._log = logging.getLogger("TestAssets")
        return super(TestBatchAppsAssets, self).setUp()


    @mock.patch.object(BatchAppsAssets, "collect_modules")
    @mock.patch("assets.AssetsUI")
    def test_create_batchappsassets(self, mock_ui, mock_collect):

        assets = BatchAppsAssets("frame", "call")
        mock_ui.assert_called_with(assets, "frame")
        mock_collect.assert_called_with()

    #@mock.patch("assets.Utils")
    #def test_start(self, mock_utils):

    #    self.mock_self.ui = mock.create_autospec(AssetsUI)
    #    started = BatchAppsAssets.start(self.mock_self)

    #    self.assertTrue(started)
    #    self.mock_self.ui.refresh.assert_called_with()

    #    self.mock_self.ui.refresh.side_effect = Exception("woops!")
    #    started = BatchAppsAssets.start(self.mock_self)

    #    self.assertFalse(started)
    #    mock_utils.error_dialog.assert_called_with("Error starting Assets UI: woops!")

    @mock.patch("assets.Assets")
    @mock.patch("assets.FileManager")
    def test_configure(self, mock_mgr, mock_assets):

        session = mock.Mock(credentials="creds", config="conf")
        self.mock_self.get_scene.return_value = "scene_name"
        BatchAppsAssets.configure(self.mock_self, session)

        mock_mgr.assert_called_with("creds", "conf")
        mock_assets.assert_called_with()
        self.assertEqual(self.mock_self.scene, "scene_name")

    def test_collect_modules(self):

        mods = BatchAppsAssets.collect_modules(self.mock_self)
        self.assertEqual(len(mods), 4)

    @mock.patch("assets.BatchAppsRenderAssets")
    @mock.patch("assets.maya")
    def test_configure_renderer(self, mock_maya, mock_default):

        mock_default.return_value = mock.Mock(render_engine = "default")
        mock_maya.mel.return_value = "test_renderer"

        renderer = mock.Mock(render_engine = "my_renderer")
        self.mock_self.modules = [renderer, "test", None]

        BatchAppsAssets.configure_renderer(self.mock_self)
        self.assertEqual(self.mock_self.renderer, mock_default.return_value)

        renderer = mock.Mock(render_engine = "test_renderer")
        self.mock_self.modules.append(renderer)

        BatchAppsAssets.configure_renderer(self.mock_self)
        self.assertEqual(self.mock_self.renderer, renderer)

    @mock.patch("assets.Assets")
    def test_refresh_asssets(self, mock_assets):

        BatchAppsAssets.refresh_assets(self.mock_self)
        mock_assets.assert_called_with()
        self.mock_self.get_scene.assert_called_with()
        self.mock_self.set_assets.assert_called_with()

    def test_set_assets(self):

        self.mock_self.manager = "manager"
        self.mock_self.renderer = mock.Mock()
        self.mock_self.assets = mock.create_autospec(Assets)
        BatchAppsAssets.set_assets(self.mock_self)

        self.mock_self.configure_renderer.assert_called_with()
        self.mock_self.assets.gather.assert_called_with("manager")

    def test_asset_categories(self):

        self.mock_self.assets = mock.create_autospec(Assets)
        self.mock_self.assets.refs = {'Additional':[], 'Caches':[], 'Textures':[]}
        cats = BatchAppsAssets.asset_categories(self.mock_self)
        self.assertEqual(sorted(cats), ['Caches', 'Textures'])

        self.mock_self.assets.refs = {'Caches':[], 'Textures':[]}
        cats = BatchAppsAssets.asset_categories(self.mock_self)
        self.assertEqual(sorted(cats), ['Caches', 'Textures'])

    def test_collect_assets(self):

        self.mock_self.assets = mock.create_autospec(Assets)
        self.mock_self.manager = mock.create_autospec(FileManager)

        self.mock_self.assets.refs = {'Additional':[]}
        self.mock_self.assets.get_pathmaps.return_value = ['/test_path', "c:\\test_path"]
        self.mock_self.manager.file_from_path.return_value = mock.create_autospec(UserFile)
        self.mock_self.manager.create_file_set.return_value = mock.create_autospec(FileCollection)

        collection = BatchAppsAssets.collect_assets(self.mock_self, ['/test_path/file1', "c:\\test_path\\file2"])
        self.assertTrue('pathmaps' in collection)
        self.assertTrue('assets' in collection)
        self.mock_self.set_assets.assert_called_with()

    def test_get_assets(self):

        self.mock_self.assets = mock.create_autospec(Assets)
        self.mock_self.assets.refs = {'Test':["file1", "file2"]}

        assets = BatchAppsAssets.get_assets(self.mock_self, "Nothing")
        self.assertEqual(assets, [])

        assets = BatchAppsAssets.get_assets(self.mock_self, "Test")
        self.assertEqual(assets, ["file1", "file2"])

    def test_add_files(self):

        self.mock_self.assets = mock.create_autospec(Assets)
        BatchAppsAssets.add_files(self.mock_self, ["a", "b"], "layout")
        self.mock_self.assets.add_asset.assert_any_call("a", "layout")
        self.mock_self.assets.add_asset.assert_any_call("b", "layout")

    def test_add_dir(self):
        
        test_dir = os.path.join(os.path.dirname(__file__), "data")
        self.mock_self.assets = mock.create_autospec(Assets)

        BatchAppsAssets.add_dir(self.mock_self, [test_dir], "layout")
        self.mock_self.assets.add_asset.assert_any_call(os.path.join(test_dir, "modules", "default.py"), "layout")
        self.assertTrue(self.mock_self.assets.add_asset.call_count >= 4)


class TestAssetsCombined(unittest.TestCase):

    @mock.patch("ui_assets.utils")
    @mock.patch("ui_assets.maya")
    @mock.patch("assets.maya")
    def test_assets(self, *args):

        mock_maya = args[0]
        mock_maya.file.return_value = "/test_path/test_scene.mb"

        mock_uimaya = args[1]
        mock_uimaya.file_select.return_value = [os.path.join(os.path.dirname(__file__), "data", "star.png")]

        def add_tab(tab):
            self.assertFalse(tab.ready)

        def call(func, *args, **kwargs):
            self.assertTrue(hasattr(func, '__call__'))
            return func()
        
        layout = mock.Mock(add_tab=add_tab)
        assets = BatchAppsAssets(layout, call)

        self.assertEqual(len(assets.modules), 4)

        creds = mock.create_autospec(Credentials)
        conf = mock.create_autospec(Configuration)
        session = mock.Mock(credentials=creds, config=conf)

        assets.configure(session)
        self.assertEqual(assets.scene, "")

        mock_maya.file.return_value = os.path.join(os.path.dirname(__file__), "data", "empty.mb")
        assets.configure(session)
        self.assertTrue(assets.scene.endswith("empty.mb"))

        assets.ui.prepare()
        self.assertTrue(assets.ui.ready)
        self.assertEqual(assets.assets.refs, {'Additional':[],
                                              'Caches':[],
                                              'Files':[]})

        files = assets.get_assets("Caches")
        self.assertEqual(files, [])

        assets.ui.add_asset()
        files = assets.get_assets("Additional")
        self.assertEqual(len(files), 1)

        asset = files[0]
        self.assertTrue(asset.included())
        self.assertTrue(asset in asset.parent_list)
        asset.exclude()
        self.assertFalse(asset in asset.parent_list)

        check_path = mock.Mock(path=mock_uimaya.file_select.return_value[0])
        self.assertTrue(asset.check([check_path]))
        check_path.path = "/test_file"
        self.assertFalse(asset.check([check_path]))

        asset.delete()

        files = assets.get_assets("Additional")
        self.assertEqual(len(files), 0)













        









        


if __name__ == '__main__':
    unittest.main()