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

import pkgutil
import inspect
import importlib

from api import MayaAPI as maya
from ui_assets import AssetsUI
from batchapps import FileManager

from default import BatchAppsRenderAssets

class BatchAppsAssets(object):
    
    def __init__(self, frame, call):

        self._log = logging.getLogger('BatchAppsMaya')
        self._call = call
        self._session = None

        self.manager = None
        self.scene = None
        self.assets = None
        self.modules = self.collect_modules()

        self.ui = AssetsUI(self, frame)

    def configure(self, session):
        self._session = session
        self.manager = FileManager(self._session.credentials, self._session.config)
        self.scene = self.get_scene()
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
        
    #def refresh_assets(self):
    #    self.assets = Assets()
    #    self.scene = self.get_scene()
    #    self.set_assets()
             
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

        if len(self.assets.refs) == 1:
            self.set_assets()

        user_files = self.assets.collect()

        for i in job_set:
            user_file = self.manager.file_from_path(i)
            user_files.append(user_file)

        collected['pathmaps'] = self.assets.get_pathmaps()
        collected['assets'] = self.manager.create_file_set(user_files)

        return collected
        

    def get_assets(self, category):
        return self.assets.refs.get(category, [])

    def get_scene(self):
        scene = os.path.abspath(maya.file(q=True, sn=True))
        if ((scene.endswith('.mb')) or (scene.endswith('.ma'))) and (os.path.exists(scene)):
            return str(os.path.normpath(scene))
        else:
            return ''

    def add_files(self, files, layout):
        for f in files:
            self.assets.add_asset(f, layout)

    def add_dir(self, dirs, layout):
        for f in dirs:
            for r, d, f in os.walk(f):
                for files in f:
                    self.assets.add_asset(os.path.join(r, files), layout)
    

class Assets(object):

    def __init__(self):

        self._log = logging.getLogger('BatchAppsMaya')
        self.manager = None
        self.refs = {'Additional': []}
        self.pathmaps = []
        
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
                self.pathmaps.append(os.path.dirname(f))
                
                try:
                    asset = Asset(self.manager.file_from_path(f), assets[key])

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
                    self.pathmaps.append(os.path.dirname(filepath))
                    asset = Asset(self.manager.file_from_path(filepath), assets['Files'])

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
            if c_path:
                self.pathmaps.append(os.path.dirname(c_path))
                asset = Asset(self.manager.file_from_path(c_path), assets['Caches'])
                assets['Caches'].append(asset)

        self._log.debug("Found {0} caches.".format(len(assets['Caches'])))
        return assets

    def add_asset(self, file, layout):
        self._log.info("Adding file: {0}".format(file))

        self.pathmaps.append(os.path.dirname(file))
        asset = Asset(self.manager.file_from_path(file), self.refs['Additional'])

        if not asset.check(self.refs['Additional']):
            asset.display(layout)
            self.refs['Additional'].append(asset)

    def get_pathmaps(self):
        path_list = list(set(self.pathmaps))
        clean_list = [str(p) for p in path_list if p]

        path_mapping = {'PathMaps':clean_list}
        return json.dumps(path_mapping)

class Asset(object):

    def __init__(self, file, parent):
        test = bool(file)
        self.path = file.path
        self.label = "    {0}".format(os.path.basename(self.path))
        self.file = file
        self.note = self.path if bool(self.file) else "Can't find {0}".format(self.path)
        self.parent_list = parent
        self.check_box = None

    def display(self, layout, enable=True):
        self.check_box = maya.check_box(label=self.label,
                                        value=bool(self.file),
                                        enable=bool(self.file),
                                        parent=layout,
                                        onCommand=lambda e: self.include(),
                                        offCommand=lambda e: self.exclude(),
                                        annotation=self.note)

    def included(self):
        if self.check_box:
            return bool(maya.check_box(self.check_box, query=True, value=True))
        else:
            return bool(self.file)

    def include(self):
        if self not in self.parent_list:
            self.parent_list.append(self)

    def exclude(self):
        try:
            self.parent_list.remove(self)
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
