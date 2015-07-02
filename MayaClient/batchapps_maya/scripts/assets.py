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

import logging
import os
import sys
import json
import glob
import time

import pkgutil
import inspect
import importlib

from api import MayaAPI as maya
from api import MayaCallbacks as callback

from utils import ProgressBar
from exception import CancellationException

from ui_assets import AssetsUI
from batchapps import FileManager

from default import BatchAppsRenderAssets

SYS_SEARCHPATHS = []
USR_SEARCHPATHS = []

class BatchAppsAssets(object):
    
    def __init__(self, frame, call):

        self._log = logging.getLogger('BatchAppsMaya')
        self._call = call
        self._session = None

        self.manager = None
        self.assets = None
        self.modules = self.collect_modules()

        self.ui = AssetsUI(self, frame)
        self.frame = frame
        callback.after_new(self.callback_refresh)
        callback.after_read(self.callback_refresh)

    def callback_refresh(self, *args):
        if self.ui.ready:
            print("refreshing")
            self.ui.refresh()

    def configure(self, session):
        self._session = session
        self.manager = FileManager(self._session.credentials, self._session.config)
        self.set_searchpaths()

        self.assets = Assets()
            
    def collect_modules(self):
        self._log.info("Collecting modules...")

        render_modules = []
        module_dir = os.environ['BATCHAPPS_MODULES']
        
        for importer, package_name, _ in pkgutil.iter_modules([module_dir]):
            if package_name == "default":
                continue

            try:
                module = importlib.import_module(package_name)
            
                for name, obj in inspect.getmembers(module, inspect.isclass): 

                    if issubclass(obj, BatchAppsRenderAssets):
                        render_modules.append(obj())

            except ImportError as err:
                self._log.warning("Couldn't import module: {0}".format(package_name))

        return render_modules

    def configure_renderer(self):
        current_renderer = maya.mel("getAttr defaultRenderGlobals.currentRenderer")
        self._log.info("Current renderer: {0}".format(current_renderer))

        for module in self.modules:

            if not hasattr(module, 'render_engine'):
                self._log.warning("Module {0} has no render engine attribute. Skipping.".format(module))
                continue

            if module.render_engine == str(current_renderer):
                self.renderer = module
                self._log.debug("Configured renderer to {0}".format(self.renderer.render_engine))
                return

        self.renderer = BatchAppsRenderAssets()
        self._log.debug("Configured renderer to {0}".format(self.renderer.render_engine))
       
             
    def set_assets(self):
        self.configure_renderer()
        self.assets.gather(self.manager)
        self.assets.extend(self.renderer.renderer_assets())

    def asset_categories(self):
        keys = self.assets.refs.keys()
        try:
            keys.remove('Additional')
        except ValueError:
            pass
        return keys

    def collect_assets(self, job_set):
        self._log.info("Converting assets into user files...")
        collected = {}

        if not self.ui.ready:
            self.ui.prepare()

        user_files = self.assets.collect()

        for i in job_set:
            user_file = self.manager.file_from_path(i)
            user_files.append(user_file)

        collected['pathmaps'] = self.assets.get_pathmaps()
        collected['assets'] = self.manager.create_file_set(user_files)

        return collected
        

    def get_assets(self, category):
        return self.assets.refs.get(category, [])

    def set_searchpaths(self):
        global SYS_SEARCHPATHS
        SYS_SEARCHPATHS = []

        scene = os.path.abspath(maya.file(q=True, sn=True))
        if ((scene.endswith('.mb')) or (scene.endswith('.ma'))) and (os.path.exists(scene)):
            SYS_SEARCHPATHS.append(os.path.dirname(scene))

        proj = maya.workspace(query=True, rootDirectory=True)
        SYS_SEARCHPATHS.append(proj)
        SYS_SEARCHPATHS.append(os.path.join(proj, "sourceImages"))
        SYS_SEARCHPATHS.append(maya.workspace(query=True, directory=True))
        SYS_SEARCHPATHS.append(os.getcwd())
        SYS_SEARCHPATHS = list(set(SYS_SEARCHPATHS))

        return SYS_SEARCHPATHS


    def add_files(self, files, layout):
        for f in files:
            self.assets.add_asset(f, layout)

    def add_dir(self, dirs, layout):
        for f in dirs:
            for r, d, f in os.walk(f):
                for files in f:
                    self.assets.add_asset(os.path.join(r, files), layout)

    def upload(self, job_set=[], progress_bar=None):

        try:

            if not job_set:
                progress_bar = ProgressBar()
                self.ui.disable(False)
                self.ui.upload_status("Checking assets... [Press ESC to cancel]")

            cancelled = False
            asset_refs = self.collect_assets(job_set)
            collection = self.manager.create_file_set(*asset_refs['assets'])


            not_uploaded = collection.is_uploaded()
            if len(not_uploaded) == 0:
                if not job_set:
                    progress_bar.end()
                raise CancellationException("File upload cancelled")

            if progress_bar.is_cancelled():
                raise CancellationException("File upload cancelled")

            progress_bar.status('Uploading files...')
            progress_bar.max(len(collection)+len(job_set))
            self.frame.select_tab(3)
            self.ui.disable(False)
            self.ui.upload_status("Uploading... [Press ESC to cancel]")
            maya.refresh()

        
            for category, assets in self.assets.refs.items():
                for index, asset in enumerate(assets):
                    if progress_bar.is_cancelled():
                        self._log.warning("File upload cancelled")
                        cancelled = True
                        break

                    asset.upload(index, upload=(asset.file in not_uploaded))
                    try: not_uploaded.remove(asset.file)
                    except: pass
                    progress_bar.step()

            for category, assets in self.assets.refs.items():
                for asset in assets:
                    asset.restore_label()

            if cancelled:
                raise CancellationException("File upload cancelled")

            if job_set and len(not_uploaded) > 0:
                def _callback(progress):
                    self.ui.upload_status("Uploading scene file - {0}% [Press ESC to cancel]".format(int(progress)))

                failed = not_uploaded.upload(force=True, callback=_callback)
                if failed:
                    for (asset, exp) in failed:
                        self._log.warning("File {0} failed with {1}".format(asset, exp))
                    raise ValueError("Failed to upload scene file")
        
            if not job_set:
                progress_bar.end()

            return collection, asset_refs["pathmaps"], progress_bar

        finally:
            self.ui.disable(True)
            self.ui.upload_status("Upload")
            maya.refresh()

    

class Assets(object):

    def __init__(self):

        self._log = logging.getLogger('BatchAppsMaya')
        self.manager = None
        self.refs = {'Additional': []}
        self.pathmaps = []
       
    def search_path(self, ref_path):

        self.pathmaps.append(os.path.dirname(ref_path))
        if os.path.exists(ref_path):
            return ref_path

        ref_file = os.path.basename(ref_path)
        searchpaths = set(USR_SEARCHPATHS + SYS_SEARCHPATHS)

        for searchpath in searchpaths:
            alt_path = os.path.join(searchpath, ref_file)

            if os.path.exists(alt_path):
                self.pathmaps.append(searchpath)
                return alt_path

        return ref_path

    def gather(self, manager):
        self.manager = manager
        self.refs = {'Additional': []}
        self.pathmaps = []

        self.refs.update(self.get_textures())
        self.refs.update(self.get_caches())
        self.refs.update(self.get_references())

    def extend(self, more_assets):
        assets = {}
        for key, value in more_assets.items():
            assets[key] = []

            for f in value:

                try:
                    checked_path = self.search_path(f)
                    asset = Asset(self.manager.file_from_path(checked_path), assets[key])

                    if not asset.check(assets[key]):
                        assets[key].append(asset)
                except:
                    continue

        self.refs.update(assets)

    def collect(self):
        self._log.info("Collecting assets...")

        userfiles = []
        for key, value in self.refs.items():
            for userfile in value:
                if userfile.included():
                    userfiles.append(userfile.file)

        self._log.debug("Found {0} external assets.".format(len(userfiles)))
        return userfiles

    def get_textures(self):
        assets = {'Files': []}

        iter_nodes = maya.dependency_nodes()
        while not iter_nodes.is_done():

            references = iter_nodes.get_references()
            for filepath in references:

                try:
                    checked_path = self.search_path(filepath)
                    asset = Asset(self.manager.file_from_path(checked_path), assets['Files'])

                    if not asset.check(assets['Files']):
                        assets['Files'].append(asset)

                except Exception as exp:
                    self._log.warning("Failed to extract asset file from reference: {0}".format(exp))
                    continue

        self._log.debug("Found {0} external files.".format(len(assets['Files'])))
        return assets

    def get_references(self):
        return {}

    def get_caches(self):
        assets = {'Caches': []}
        cacheFiles = maya.get_list(type="cacheFile")

        for c in cacheFiles:

            c_path = maya.get_attr(c+".cachePath")
            c_name = maya.get_attr(c+".cacheName")

            if c_path and c_name:
                self.pathmaps.append(c_path)
                full_path = os.path.join(c_path + c_name)
                path_matches = glob.glob(full_path + "*")
                for cache_path in path_matches:
                    asset = Asset(self.manager.file_from_path(cache_path), assets['Caches'])
                    assets['Caches'].append(asset)

        self._log.debug("Found {0} caches.".format(len(assets['Caches'])))
        return assets

    def add_asset(self, file, layout):
        self._log.info("Adding file: {0}".format(file))

        self.pathmaps.append(os.path.dirname(file))
        asset = Asset(self.manager.file_from_path(file), self.refs['Additional'])

        if not asset.check(self.refs['Additional']):
            asset.display(*layout)
            self.refs['Additional'].append(asset)

    def get_pathmaps(self):
        path_list = list(set(self.pathmaps))
        clean_list = [str(p) for p in path_list if p]

        path_mapping = {'PathMaps':clean_list}
        return path_mapping

class Asset(object):

    def __init__(self, file, parent):
        self.path = file.path
        self.label = "    {0}".format(os.path.basename(self.path))
        self.file = file
        self.note = self.path if bool(self.file) else "Can't find {0}".format(self.path)
        self.parent_list = parent
        self.check_box = None

    def display(self, layout, scroll):
        self.scroll_layout=scroll
        found = bool(self.file)
        current_children = maya.col_layout(layout, query=True, childArray=True)
        if current_children is None:
            self.index = 0
        else:
            self.index = len(current_children)/2

        if found:
            self.check_box = maya.symbol_check_box(value=True,
                                            parent=layout,
                                            onCommand=lambda e: self.include(),
                                            offCommand=lambda e: self.exclude(),
                                            annotation="Click to remove asset from submission")

        else:
            self.check_box = maya.symbol_button("out_aimConstraint.png",
                                            parent=layout,
                                            command=lambda e: self.search(),
                                            height=17,
                                            annotation="Add search path")

        self.display_text = maya.text(self.label, parent=layout, enable=found, annotation=self.note, align="left")


    def included(self):
        if self.check_box and bool(self.file):
            return bool(maya.symbol_check_box(self.check_box, query=True, value=True))
        else:
            return bool(self.file)

    def include(self):
        if self not in self.parent_list:
            self.parent_list.append(self)
        maya.symbol_check_box(self.check_box, edit=True, annotation="Click to remove asset from submission")

    def search(self):
        global USR_SEARCHPATHS

        cap = "Select directory of assets"
        okCap = "Add Search Path"
        new_dir = maya.file_select(fileMode=3, okCaption=okCap, caption=cap)
        if not new_dir:
            return

        USR_SEARCHPATHS.append(new_dir[0])
        maya.warning("New search path added. Click Refresh.")

    def exclude(self):
        try:
            self.parent_list.remove(self)
            maya.symbol_check_box(self.check_box, edit=True, annotation="Click to include asset in submission")
        except ValueError:
            pass

    def delete(self):
        try:
            self.parent_list.remove(self)
        except ValueError:
            pass
        maya.delete_ui(self.check_box, control=True)

    def check(self, files):
        return any(os.path.normcase(f.path) == os.path.normcase(self.path) for f in files)

    def restore_label(self):
        maya.text(self.display_text, edit=True, label=self.label)

    def make_visible(self, index):
        if index == 0:
            maya.scroll_layout(self.scroll_layout, edit=True, scrollPage="up")
        
        elif index >= 4:
            maya.scroll_layout(self.scroll_layout, edit=True, scrollByPixel=("down",17))

        maya.refresh()

    def upload(self, index, upload=True):
        self.make_visible(index)
        name = os.path.basename(self.path)

        if upload:
            def progress(prog):
                maya.text(self.display_text, edit=True, label="    Uploading {0}% {1}".format(int(prog), name))
                maya.refresh()

            uploaded = self.file.upload(force=True, callback=progress)
            if not uploaded.success:
                raise ValueError("Upload failed for {0}: {1}".format(name, uploaded.result))

        elif self.included():
            maya.text(self.display_text, edit=True, label="    Already uploaded {0}".format(name))
            maya.refresh()

        else:
            maya.text(self.display_text, edit=True, label="    Skipped {0}".format(name))
            maya.refresh()

