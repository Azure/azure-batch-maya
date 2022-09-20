# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
import os
import logging
import json
from Queue import Queue

# win32-specific imports
try:
    import pywintypes
    import win32con
    import win32net
    import win32netcon
    import win32security
    import winerror
except ImportError:
    pass

if sys.version_info >= (3, 3):
    import unittest2 as unittest
    from unittest.mock import MagicMock
else:
    import unittest
    import mock
    from mock import MagicMock

from azure import batch_extensions

from ui_assets import AssetsUI
from assets import Asset, Assets, AzureBatchAssets
from exception import FileUploadException
from azurebatchutils import ProgressBar, ProcButton

class TestAsset(unittest.TestCase):
    
    def setUp(self):
        self.mock_self = mock.create_autospec(Asset)
        self.mock_file = "/my/local/test_path"
        self.mock_self.batch = mock.create_autospec(batch_extensions.BatchExtensionsClient)
        self.mock_self.batch.file = mock.create_autospec(batch_extensions.operations.ExtendedFileOperations)
        self.mock_self.log = logging.getLogger('batch-maya-asset-tests')
        return super(TestAsset, self).setUp()
    
    def test_asset_create(self):
        test_asset = Asset(self.mock_file, "parent", "batch")
        self.assertEqual(test_asset.label, "    test_path")

        expected_path = os.path.realpath(self.mock_file)
        expected_directory = os.path.dirname(expected_path)

        self.assertEqual(test_asset.path, expected_path)
        self.assertEqual(test_asset.note, "Can't find " + expected_path)
        self.assertFalse(test_asset.exists)

        with mock.patch.object(os.path, 'exists') as exist:
            with mock.patch.object(os.path, 'getmtime') as mod:
                with mock.patch.object(os.path, 'getsize'):
                    exist.return_value = True
                    mod.return_value = 1453766301
                    test_asset = Asset(self.mock_file, "parent", "batch")
                    self.assertEqual(test_asset.note, expected_path)
                    self.assertTrue(test_asset.exists)
                    self.assertTrue(test_asset.pathmap[expected_directory]('Linux').endswith('my/local'))

    @mock.patch("assets.maya")
    def test_asset_display(self, mock_api):
        self.mock_self.path = "\\my\\local\\test_path"
        self.mock_self.label = "label"
        self.mock_self.note = "note"
        self.mock_self.exists = False
        
        Asset.display(self.mock_self, "ui", "layout", "scroll")
        mock_api.symbol_button.assert_called_with(
            image="fpe_someBrokenPaths.png", parent="layout", command=mock.ANY,
            height=17, annotation="Add search path")
        mock_api.text.assert_called_with("label", parent="layout", enable=False, annotation="note", align="left")
        self.assertEqual(self.mock_self.scroll_layout, "scroll")
        self.assertEqual(self.mock_self.frame, "ui")

        self.mock_self.exists = True
        Asset.display(self.mock_self, "ui", "layout", "scroll")
        mock_api.symbol_check_box.assert_called_with(
            annotation='Click to remove asset from submission', offCommand=mock.ANY,
            onCommand=mock.ANY, parent='layout', value=True)

    @mock.patch("assets.maya")
    def test_asset_included(self, mock_api):
        self.mock_self.exists = False
        self.mock_self.check_box = None

        val = Asset.included(self.mock_self)
        self.assertFalse(val)

        self.mock_self.check_box = 1
        val = Asset.included(self.mock_self)
        self.assertFalse(val)

        self.mock_self.exists = True
        val = Asset.included(self.mock_self)
        mock_api.symbol_check_box.assert_called_with(1, query=True, value=True)

    @mock.patch("assets.maya")
    def test_asset_include(self, mock_api):
        self.mock_self.check_box = 1
        self.mock_self.parent_list = []
        Asset.include(self.mock_self)
        self.assertEqual(self.mock_self.parent_list, [self.mock_self])
        mock_api.symbol_check_box.assert_called_with(1, edit=True, annotation="Click to remove asset from submission")

        Asset.include(self.mock_self)
        self.assertEqual(self.mock_self.parent_list, [self.mock_self])
        mock_api.symbol_check_box.assert_called_with(1, edit=True, annotation="Click to remove asset from submission")

    @mock.patch("assets.maya")
    def test_asset_search(self, mock_api):
        from assets import USR_SEARCHPATHS
        self.mock_self.frame = mock.create_autospec(AssetsUI)
        mock_api.file_select.return_value = None
        Asset.search(self.mock_self)
        self.assertEqual(USR_SEARCHPATHS, [])
        self.assertEqual(self.mock_self.frame.refresh.call_count, 0)

        mock_api.file_select.return_value = []
        Asset.search(self.mock_self)
        self.assertEqual(USR_SEARCHPATHS, [])
        self.assertEqual(self.mock_self.frame.refresh.call_count, 0)

        mock_api.file_select.return_value = ["selected_path"]
        Asset.search(self.mock_self)
        self.assertEqual(USR_SEARCHPATHS, ["selected_path"])
        self.mock_self.frame.refresh.assert_called_with()

    @mock.patch("assets.maya")
    def test_asset_exclude(self, mock_api):
        self.mock_self.check_box = 1
        self.mock_self.parent_list = []
        Asset.exclude(self.mock_self)
        self.assertEqual(self.mock_self.parent_list, [])
        self.assertEqual(mock_api.symbol_check_box.call_count, 0)

        self.mock_self.parent_list = ["test"]
        Asset.exclude(self.mock_self)
        self.assertEqual(self.mock_self.parent_list, ["test"])
        self.assertEqual(mock_api.symbol_check_box.call_count, 0)

        self.mock_self.parent_list = [self.mock_self]
        Asset.exclude(self.mock_self)
        self.assertEqual(self.mock_self.parent_list, [])
        mock_api.symbol_check_box.assert_called_with(1, edit=True, annotation="Click to include asset in submission")

    @mock.patch("assets.maya")
    def test_asset_delete(self, mock_api):
        self.mock_self.parent_list = []
        self.mock_self.check_box = 1

        Asset.delete(self.mock_self)
        mock_api.delete_ui.assert_called_with(1, control=True)
        self.assertEqual(self.mock_self.parent_list, [])

        self.mock_self.parent_list = [self.mock_self]
        Asset.delete(self.mock_self)
        mock_api.delete_ui.assert_called_with(1, control=True)
        self.assertEqual(self.mock_self.parent_list, [])

    def test_asset_check(self):
        new_file = mock.create_autospec(Asset)
        new_file.path = "C:\\TEST_file\\WeiRD_path"
        self.mock_self.path = "c:\\test_file\\Weird_path"

        check = Asset.is_duplicate(self.mock_self, [new_file])
        self.assertTrue(check)

        new_file.path = "C:\\TEST_file\\WeiRD_path\\different"
        check = Asset.is_duplicate(self.mock_self, [new_file])
        self.assertFalse(check)

    @mock.patch("assets.maya")
    def test_asset_make_visible(self, mock_maya):
        mock_maya.text.return_value = 17
        self.mock_self.scroll_layout = "layout"
        self.mock_self.display_text = "text"
        self.called = 0

        def scroll(*args, **kwargs):
            self.called += 1
            if kwargs.get("query") and self.mock_self.scroll_layout == "layout":
                return [4,0]
            elif kwargs.get("query"):
                return [0,0]
            else:
                self.assertEqual(kwargs.get("scrollPage"), "up")
                self.mock_self.scroll_layout = "scrolled"

        mock_maya.scroll_layout = scroll
        Asset.make_visible(self.mock_self, 0)
        self.assertEqual(self.called, 3)

        def scroll(*args, **kwargs):
            self.called += 1
            self.assertEqual(kwargs.get("scrollByPixel"), ("down",17))

        mock_maya.scroll_layout = scroll
        Asset.make_visible(self.mock_self, 5)
        self.assertEqual(self.called, 4)

    @mock.patch("assets.maya")
    def test_asset_upload(self, mock_maya):

        queue = Queue()
        self.mock_self.path = "/my/test/path/file.txt"
        self.mock_self.display_text = "display"
        self.mock_self.included.return_value = False
        self.mock_self.storage_path = "my/test/path/file.txt"
        self.mock_self.size = 10
        prog = mock.create_autospec(ProgressBar)
        prog.done = False

        Asset.upload(self.mock_self, 0, prog, queue, "container")
        self.mock_self.batch.file.upload.assert_called_with(
            "/my/test/path/file.txt", "container", "my/test/path/file.txt", progress_callback=mock.ANY)
        self.assertEqual(queue.qsize(), 6)

        self.mock_self.batch.file.upload.side_effect = ValueError('boom')
        Asset.upload(self.mock_self, 0, prog, queue, "container")
        self.assertEqual(queue.qsize(), 11)

        prog.done = True
        Asset.upload(self.mock_self, 0, prog, queue, "container")
        self.assertEqual(queue.qsize(), 12)


class TestAssets(unittest.TestCase):

    def setUp(self):
        self.mock_self = mock.create_autospec(Assets)
        self.mock_self._log = logging.getLogger("TestAssets")
        self.mock_self.batch = mock.create_autospec(batch_extensions.BatchExtensionsClient)
        return super(TestAssets, self).setUp()

    def test_assets_create(self):
        test_assets = Assets('batch')
        self.assertEqual(test_assets.batch, 'batch')
        self.assertEqual(test_assets.refs, [])

    @mock.patch("assets.SYS_SEARCHPATHS")
    @mock.patch("assets.USR_SEARCHPATHS")
    @mock.patch("assets.glob")
    @mock.patch("assets.os.path.exists")
    def test_assets_search_path(self, mock_exists, mock_glob, mock_sys, mock_usr):
        mock_sys = []
        mock_usr = []
        self.mock_self.pathmaps = {}
        mock_exists.return_value = True

        path = Assets._search_path(self.mock_self, "testpath\\testfile")
        self.assertEqual(path, ["testpath\\testfile"])
        mock_exists.assert_called_once_with("testpath\\testfile")
        mock_exists.call_count = 0
        self.assertEqual(mock_glob.glob.call_count, 0)

        mock_exists.return_value = False
        path = Assets._search_path(self.mock_self, "testpath\\testfile")
        self.assertEqual(path, ["testpath\\testfile"])
        mock_exists.assert_called_once_with("testpath\\testfile")
        self.assertEqual(mock_glob.glob.call_count, 0)

        mock_glob.glob.return_value = [1,2,3]
        path = Assets._search_path(self.mock_self, "testpath\\*\\testfile")
        mock_glob.glob.assert_called_with("testpath\\*\\testfile")
        self.assertEqual(path, [1,2,3])

        mock_glob.glob.return_value = []
        path = Assets._search_path(self.mock_self, "testpath\\[0-9]testfile")
        mock_glob.glob.assert_any_call("testpath\\[0-9]testfile")
        self.assertEqual(path, ["testpath\\[0-9]testfile"])

    def test_assets_gather(self):
        self.mock_self.refs = []
        self.mock_self._get_textures.return_value = ['a']
        self.mock_self._get_caches.return_value = ['b']
        self.mock_self._get_references.return_value = ['c']

        Assets.gather(self.mock_self)
        self.assertEqual(self.mock_self.refs, ['a', 'b', 'c'])
        self.assertEqual(self.mock_self._get_textures.call_count, 1)
        self.assertEqual(self.mock_self._get_caches.call_count, 1)
        self.assertEqual(self.mock_self._get_references.call_count, 1)

    @mock.patch("assets.Asset")
    def test_assets_extend(self, mock_asset):
        self.mock_self.refs = []
        mock_asset.return_value = mock.create_autospec(Asset)
        mock_asset.return_value.is_duplicate.return_value = True
        self.mock_self._search_path.return_value = ["a"]

        Assets.extend(self.mock_self, ["/test_path/test_file"])
        mock_asset.assert_called_with("a", [], self.mock_self.batch, self.mock_self._log)
        self.assertEqual(self.mock_self.refs, [])

        mock_asset.return_value.is_duplicate.return_value = False
        Assets.extend(self.mock_self, ["/test_path/test_file"])
        self.assertEqual(self.mock_self.refs, [mock.ANY])

        self.mock_self.refs = []
        mock_asset.side_effect = Exception("error!")
        Assets.extend(self.mock_self, ["/test_path/test_file"])
        self.assertEqual(self.mock_self.refs, [])

    def test_assets_collect(self):
        self.mock_self.refs = []
        files = Assets.collect(self.mock_self)
        self.assertEqual(files, [])

        test_file = mock.create_autospec(Asset)
        test_file.included.return_value = True
        self.mock_self.refs = [test_file]
        files = Assets.collect(self.mock_self)
        test_file.included.assert_called_once_with()
        self.assertEqual(files, [test_file])

        test_file.included.return_value = False
        files = Assets.collect(self.mock_self)
        self.assertEqual(files, [])

    @mock.patch("assets.Asset")
    @mock.patch("assets.maya")
    def test_assets_get_textures(self, mock_maya, mock_asset):
        mock_asset.return_value = mock.create_autospec(Asset)
        mock_asset.return_value.is_duplicate.return_value = True
        self.mock_self._search_path.return_value = ["a"]

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
        tex = Assets._get_textures(self.mock_self)
        self.assertEqual(tex, [])
        self.assertEqual(mock_asset.call_count, 15)
        mock_asset.assert_called_with("a", [], self.mock_self.batch, self.mock_self._log)

        mock_asset.return_value.is_duplicate.return_value = False
        mock_maya.dependency_nodes.return_value = TestIter()
        tex = Assets._get_textures(self.mock_self)
        self.assertEqual(len(tex), 15)

    @mock.patch("assets.Asset")
    @mock.patch("assets.maya")
    def test_assets_get_references(self, mock_maya, mock_asset):
        mock_asset.return_value = mock.create_autospec(Asset)
        mock_asset.return_value.is_duplicate.return_value = True
        self.mock_self.refs = []

        refs = Assets._get_references(self.mock_self)
        self.assertEqual(refs, [])

        mock_maya.get_list.return_value = ["1", "2", "3"]
        mock_maya.reference.return_value = "c:\\file\\ref"
        refs = Assets._get_references(self.mock_self)
        self.assertEqual(refs, [])

        mock_asset.return_value.is_duplicate.return_value = False
        refs = Assets._get_references(self.mock_self)
        self.assertEqual(refs, [mock.ANY])

    @mock.patch("assets.Asset")
    @mock.patch("assets.maya")
    @mock.patch("assets.glob")
    def test_assets_get_caches(self, mock_glob, mock_maya, mock_asset):
        def get_attr(node):
            if node.endswith("cachePath"):
                return "/test_path"
            else:
                return "test_file"
        mock_asset.return_value = mock.create_autospec(Asset)
        mock_maya.get_list.return_value = ["1", "2", "3"]
        mock_maya.get_attr = get_attr
        mock_glob.glob.return_value = ["pathA"]

        caches = Assets._get_caches(self.mock_self)
        self.assertEqual(caches, [mock.ANY, mock.ANY, mock.ANY])

    @mock.patch("assets.Asset")
    def test_assets_add_asset(self, mock_asset):
        self.mock_self.refs = []
        mock_asset.return_value = mock.create_autospec(Asset)
        mock_asset.return_value.is_duplicate.return_value = True

        Assets.add_asset(self.mock_self, "/test_path/my_asset", "ui", "layout", "scroll")
        self.assertEqual(self.mock_self.refs, [])
        mock_asset.return_value.is_duplicate.assert_called_once_with([])
        mock_asset.assert_called_once_with("/test_path/my_asset", [], self.mock_self.batch, self.mock_self._log)

        mock_asset.return_value.is_duplicate.return_value = False
        Assets.add_asset(self.mock_self, "/test_path/my_asset", "ui", "layout", "scroll")
        self.assertEqual(self.mock_self.refs, [mock.ANY])
        mock_asset.return_value.display.assert_called_with("ui", "layout", "scroll")


class TestAzureBatchAssets(unittest.TestCase):

    def setUp(self):
        self.mock_self = mock.create_autospec(AzureBatchAssets)
        self.mock_self._log = logging.getLogger("TestAssets")
        self.mock_self.batch = mock.create_autospec(batch_extensions.BatchExtensionsClient)
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
        os.environ["AZUREBATCH_VERSION"] = "0.1"
        return super(TestAzureBatchAssets, self).setUp()


    @mock.patch.object(AzureBatchAssets, "_collect_modules")
    @mock.patch("assets.callback")
    @mock.patch("assets.AssetsUI")
    def test_batchassets_create(self, mock_ui, mock_call, mock_collect):
        assets = AzureBatchAssets(3, "frame", "call")
        mock_ui.assert_called_with(assets, "frame")
        mock_collect.assert_called_with()
        #mock_call.after_new.assert_called_with(assets.callback_refresh)
        #mock_call.after_read.assert_called_with(assets.callback_refresh)

    def test_batchassets_callback_refresh(self):
        self.mock_self.ui = mock.create_autospec(AssetsUI)
        self.mock_self.frame = mock.Mock()
        self.mock_self.frame.selected_tab =  lambda: 1
        self.mock_self.ui.ready = False

        AzureBatchAssets._callback_refresh(self.mock_self)
        self.assertEqual(self.mock_self.ui.refresh.call_count, 0)
        self.assertFalse(self.mock_self.ui.ready)

        self.mock_self.ui.ready = True
        AzureBatchAssets._callback_refresh(self.mock_self)
        self.assertEqual(self.mock_self.ui.refresh.call_count, 0)
        self.assertFalse(self.mock_self.ui.ready)

        self.mock_self.frame.selected_tab =  lambda: 3
        AzureBatchAssets._callback_refresh(self.mock_self)
        self.assertEqual(self.mock_self.ui.refresh.call_count, 1)        

    @mock.patch("assets.Assets")
    def test_batchassets_configure(self, mock_assets):
        session = mock.Mock(batch="batch")
        AzureBatchAssets.configure(self.mock_self, session, None, None)
        mock_assets.assert_called_with("batch")
        self.assertEqual(self.mock_self._set_searchpaths.call_count, 1)

    def test_batchassets_collect_modules(self):
        mods = AzureBatchAssets._collect_modules(self.mock_self)
        self.assertEqual(len(mods), 4)

    @mock.patch("azurebatchutils.get_current_scene_renderer")
    @mock.patch("assets.maya")
    def test_batchassets_configure_renderer(self, mock_maya,  mock_renderer):
        mock_renderer.return_value = "test_renderer"

        renderer = mock.Mock(render_engine = "my_renderer")
        self.mock_self.modules = [renderer, "test", None]

        AzureBatchAssets._configure_renderer(self.mock_self)
        self.assertEqual(self.mock_self.renderer.render_engine, "Renderer_Default")

        renderer = mock.Mock(render_engine = "test_renderer")
        self.mock_self.modules.append(renderer)

        AzureBatchAssets._configure_renderer(self.mock_self)
        self.assertEqual(self.mock_self.renderer.render_engine, renderer.render_engine)

    def test_batchassets_set_assets(self):
        self.mock_self.renderer = mock.Mock()
        self.mock_self._assets = mock.create_autospec(Assets)
        AzureBatchAssets.set_assets(self.mock_self)
        self.mock_self._configure_renderer.assert_called_with()
        self.mock_self._assets.gather.assert_called_with()
        self.mock_self._assets.extend.assert_called_with(mock.ANY)

    def test_batchassets_get_assets(self):
        self.mock_self._assets = mock.create_autospec(Assets)
        self.mock_self._assets.refs = ["file1", "file2"]
        assets = AzureBatchAssets.get_assets(self.mock_self)
        self.assertEqual(assets, ["file1", "file2"])

    @mock.patch("azurebatchutils.get_root_dir")
    @mock.patch("assets.SYS_SEARCHPATHS")
    @mock.patch("assets.maya")
    def test_batchassets_set_searchpaths(self, mock_maya, mock_syspaths, mock_utils):
        mock_maya.file.return_value = "testscene.mb"
        mock_maya.workspace.return_value = "/test/directory"
        mock_utils.return_value = "/test/directory"
        mock_syspaths = ["a", "b", "c"]
        paths = AzureBatchAssets._set_searchpaths(self.mock_self)
        self.assertEqual(sorted(paths), ["/test/directory", "/test/directory\\sourceimages", os.getcwd()])

    def test_batchassets_add_files(self):
        self.mock_self.ui = mock.Mock()
        self.mock_self._assets = mock.create_autospec(Assets)
        AzureBatchAssets.add_files(self.mock_self, ["a", "b"], "layout", "scroll")
        self.mock_self._assets.add_asset.assert_any_call("a", self.mock_self.ui, "layout", "scroll")
        self.mock_self._assets.add_asset.assert_any_call("b", self.mock_self.ui, "layout", "scroll")

    def test_batchassets_add_dir(self):
        test_dir = os.path.join(os.path.dirname(__file__), "data")
        self.mock_self._assets = mock.create_autospec(Assets)
        self.mock_self.ui = mock.Mock()
        AzureBatchAssets.add_dir(self.mock_self, [test_dir], "layout", "scroll")
        self.mock_self._assets.add_asset.assert_any_call(os.path.join(test_dir, "modules", "default.py"),
                                                         self.mock_self.ui, "layout", "scroll")
        self.assertTrue(self.mock_self._assets.add_asset.call_count >= 4)

    @mock.patch("assets.Asset")
    @mock.patch("assets.ProgressBar")
    @mock.patch("assets.maya")
    def test_batchassets_upload(self, mock_maya, mock_prog, mock_asset):
        # TODO
        self.mock_self.ui = mock.create_autospec(AssetsUI)
        self.mock_self.ui.upload_button = mock.create_autospec(ProcButton)
        self.mock_self._assets = mock.create_autospec(Assets)
        AzureBatchAssets.upload(self.mock_self)

    @mock.patch.object(AzureBatchAssets, "_collect_modules")
    @mock.patch("assets.callback")
    @mock.patch("assets.AssetsUI")
    def test_temp_dir_access(self, mock_ui, mock_call, mock_collect):
        if sys.platform != "win32":
            return
        aba = AzureBatchAssets(0, "frame", "call")
        # create temporary user
        username = "tempuser"
        password = "Password123"
        user_info = {
            "name": username,
            "password": password,
            "priv": win32netcon.USER_PRIV_USER,
            "flags": 0
        }
        try:
            win32net.NetUserAdd(None, 1, user_info)
        except pywintypes.error as e:
            if e.winerror == winerror.ERROR_ACCESS_DENIED:
                raise Exception("test must be run as admin to create temp user")
            else:
                raise e
        # make temp user admin
        sid, domain, at = win32security.LookupAccountName(None, username)
        win32net.NetLocalGroupAddMembers(None, "Administrators", 0, [{"sid": sid}])
        # impersonate temporary user
        handle = win32security.LogonUser(username, None, password, win32con.LOGON32_LOGON_INTERACTIVE, win32con.LOGON32_PROVIDER_DEFAULT)
        win32security.ImpersonateLoggedOnUser(handle)
        # try to access the temp directory
        accessed = os.access(aba._temp_dir, os.W_OK)
        # revert impersonation and delete temp user
        win32security.RevertToSelf()
        handle.close()
        win32net.NetUserDel(None, username)
        
        self.assertFalse(accessed, "_temp_dir should be inaccessible for other users")

if __name__ == '__main__':
    unittest.main()