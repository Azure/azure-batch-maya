# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import unicode_literals

import logging
from datetime import datetime
import threading
import os
import sys
import glob
import pkgutil
import inspect
import importlib
import tempfile
import re
from Queue import Queue

from azure.batch_extensions import _file_utils as fileutils

from azurebatchmayaapi import MayaAPI as maya
from azurebatchmayaapi import MayaCallbacks as callback

import azurebatchutils as utils
from azurebatchutils import ProgressBar
from exception import CancellationException, FileUploadException

from ui_assets import AssetsUI
from default import AzureBatchRenderAssets


SYS_SEARCHPATHS = []
USR_SEARCHPATHS = []
BYTES = 1024
try:
    str = unicode
except NameError:
    pass


class AzureBatchAssets(object):
    """Handler for asset file functionality."""
    
    def __init__(self, index, frame, call):
        """Create new Asset Handler.

        :param index: The UI tab index.
        :param frame: The shared plug-in UI frame.
        :type frame: :class:`.AzureBatchUI`
        :param func call: The shared REST API call wrapper.
        """
        self._log = logging.getLogger('AzureBatchMaya')
        self._call = call
        self._session = None
        self._assets = None
        self._tab_index = index
        self._upload_threads = None

        self.batch = None
        self.modules = self._collect_modules()
        self.ui = AssetsUI(self, frame)
        self.frame = frame

        #callback.after_new(self._callback_refresh)
        #callback.after_read(self._callback_refresh)

    def _callback_refresh(self, *args):
        """Called by Maya when a new scene file is loaded, so we reset
        the asset and submission pages of the UI, as the file references
        and potentially the selected render engine will have changed.
        """
        global USR_SEARCHPATHS
        USR_SEARCHPATHS = []
        self._set_searchpaths()

        if self.frame.selected_tab() == 3:
            # We only want to do a full refresh if Assets is the current tab
            self.ui.refresh()
        elif self.ui.ready:
            # Otherwise we'll just reset it to be more efficient
            self.ui.ready = False

    def _collect_modules(self):
        """Collect the renderer-specific submission modules. This is where
        the renderer-specfic asset collection is defined.
        """
        self._log.info("Collecting modules...")
        render_modules = []
        module_dir = os.environ['AZUREBATCH_MODULES']
        
        for importer, package_name, _ in pkgutil.iter_modules([module_dir]):
            if package_name == "default":
                continue
            try:
                module = importlib.import_module(package_name)
                for name, obj in inspect.getmembers(module, inspect.isclass): 
                    if issubclass(obj, AzureBatchRenderAssets):
                        render_modules.append(obj())
            except ImportError as err:
                self._log.warning("Couldn't import module: {0}".format(package_name))
        return render_modules

    def _set_searchpaths(self):
        """Set the search path collection that will be used to resolve relative or
        invalid asset reference paths. This is reset each time a new file is loaded
        as we use the current location of the scene file as a search path.
        We also use the current project directory, the sourceimages directory and the
        current working directory.
        """
        global SYS_SEARCHPATHS
        SYS_SEARCHPATHS = []
        scene = os.path.abspath(maya.file(q=True, sn=True))
        if ((scene.endswith('.mb')) or (scene.endswith('.ma'))) and (os.path.exists(scene)):
            SYS_SEARCHPATHS.append(os.path.dirname(scene))
        proj = utils.get_root_dir()
        SYS_SEARCHPATHS.append(proj)
        SYS_SEARCHPATHS.append(os.path.join(proj, "sourceimages"))
        SYS_SEARCHPATHS.append(maya.workspace(query=True, directory=True))
        SYS_SEARCHPATHS.append(os.getcwd())
        SYS_SEARCHPATHS = list(set(SYS_SEARCHPATHS))
        return SYS_SEARCHPATHS

    def _configure_renderer(self):
        """Configure the renderer-specific asset collection according
        to the currently selected render engine.
        Only called by the set_assets function, which is called on loading and
        refreshing the assets tab.
        """
        current_renderer = maya.get_attr("defaultRenderGlobals.currentRenderer")
        self._log.info("Current renderer: {0}".format(current_renderer))

        for module in self.modules:
            if not hasattr(module, 'render_engine'):
                self._log.warning("Module {0} has no render engine attribute. Skipping.".format(module))
                continue
            if module.render_engine == str(current_renderer):
                self.renderer = module
                self._log.debug("Configured renderer to {0}".format(self.renderer.render_engine))
                return
        self.renderer = AzureBatchRenderAssets()
        self._log.debug("Configured renderer to {0}".format(self.renderer.render_engine))

    def _switch_tab(self):
        """Make this tab the currently displayed tab. If this tab is already
        open, this will do nothing.
        """
        self.frame.select_tab(self._tab_index)

    def _collect_assets(self):
        """Called on upload. If the asset tab has not yet been loaded before
        job submission is attempted, then the asset references have not yet
        been populated, so gathers the assets if they need it, otherwise return
        the current list of asset references.
        """
        if not self.ui.ready:
            self.ui.prepare()
        return self._assets.collect()

    def _create_remote_workspace(self, os_flavor):
        """Create a custom workspace file to set as the remote rendering project.
        :param str os_flavor: The chosen operating system of the render nodes, used
         to determine the formatting of the path remapping.
        """
        proj_file = os.path.join(tempfile.gettempdir(), "workspace.mel")
        with open(proj_file, 'w') as handle:
            for rule in maya.workspace(fileRuleList=True):
                project_dir = maya.workspace(fileRuleEntry=rule)
                remote_path = utils.get_remote_directory(maya.workspace(en=project_dir), os_flavor)
                if os_flavor == utils.OperatingSystem.windows:
                    full_remote_path = "X:\\\\" + remote_path
                else:
                    full_remote_path = "/X/" + remote_path
                mapped_dir = "workspace -fr \"{}\" \"{}\";\n".format(rule, full_remote_path)
                handle.write(mapped_dir.encode('utf-8'))
        return Asset(proj_file, [], self.batch, self._log)

    def _create_path_map(self, plugins, os_flavor):
        """Create the pre-render mel script to redirect all the asset reference
        directories for this render. Called on job submission, and the resulting
        file is uploaded as an asset to the current file group.
        Also returns a formatted list of cloud destination directories as
        search paths that can be used according to renderer.

        :param plugins: A list of the currently enabled plugins, so that these can
         also be enabled on the server.
        :param str os_flavor: The chosen operating system of the render nodes, used
         to determine the formatting of the path remapping.
        """
        map_file = os.path.join(tempfile.gettempdir(), "asset_map.mel")
        pathmap = dict(self._assets.pathmaps)
        for asset in self._assets.refs:
            pathmap.update(asset.pathmap)
        cloud_paths = []
        with open(map_file, 'w') as handle:
            handle.write("global proc renderPrep()\n")
            handle.write("{\n")
            if plugins:
                for plugin in plugins:
                    handle.write("loadPlugin \"{}\";\n".format(plugin.encode('utf-8')))
            handle.write("dirmap -en true;\n")
            for local, remote in pathmap.items():
                if os_flavor == utils.OperatingSystem.windows:
                    full_remote_path = "X:\\\\" + remote(os_flavor)
                else:
                    full_remote_path = "/X/" + remote(os_flavor)
                parsed_local = local.replace('\\', '\\\\')
                cloud_paths.append(full_remote_path)
                map_cmd = "dirmap -m \"{}\" \"{}\";\n".format(parsed_local, full_remote_path)
                handle.write(map_cmd.encode('utf-8'))
            self.renderer.setup_script(handle, pathmap, cloud_paths)
            handle.write("}")
        return Asset(map_file, [], self.batch, self._log), ';'.join(cloud_paths)

    def _upload_all(self, to_upload, progress, total, project):
        """Upload all selected assets in configured number of threads."""
        uploads_running = []
        progress_queue = Queue()
        threads = self._upload_threads()
        self._log.debug("Uploading assets in {} threads.".format(threads))
        for i in range(0, len(to_upload), threads):
            for index, asset in enumerate(to_upload[i:i + threads]):
                self._log.debug("Starting thread for asset: {}".format(asset.path))
                upload = threading.Thread(
                    target=asset.upload, args=(index, progress, progress_queue, project))
                upload.start()
                uploads_running.append(upload)
            self._log.debug("Batch of asset uploads pending: {}".format(threading.active_count()))
            while any(t for t in uploads_running if t.is_alive()) or not progress_queue.empty():
                uploaded = progress_queue.get()
                if isinstance(uploaded, Exception):
                    raise uploaded
                elif callable(uploaded):
                    uploaded()
                else:
                    total = total - (uploaded/BYTES/BYTES)
                    self.ui.upload_status("Uploading {0}...".format(self._format_size(total)))
                progress_queue.task_done()

    def _format_size(self, nbytes):
        """Format the data size in bytes to nicely display
        for upload progress.
        """
        suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
        if nbytes == 0:
            return '0 B'
        i = 0
        while nbytes >= BYTES and i < len(suffixes)-1:
            nbytes /= BYTES
            i += 1
        f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
        return '%s %s' % (f, suffixes[i])

    def _total_data(self, files):
        """Format the combined size of the files to display
        for upload progress.
        """
        data = float(0)
        for asset in files:
            data += asset.size
        return data/BYTES/BYTES

    def configure(self, session):
        """Populate the Batch client for the current sessions of the asset tab.
        Called on successful authentication.
        """
        self._session = session
        self._upload_threads = session.get_threads
        self.batch = self._session.batch
        self._set_searchpaths()
        self._assets = Assets(self.batch)

    def generate_sas_token(self, file_group):
        """Generate SAS token for file group container with read and list
        permissions.
        TODO: Move this into BatchExtensions file utils.
        """
        container_name = fileutils.get_container_name(file_group)
        container_url = fileutils.generate_container_sas_token(
            container_name,
            self.batch.file.get_storage_client(),
            permission='rl')
        return container_url
        
    def set_assets(self):
        """Gather the asset references of the scene for display in the
        asset tab. Called on loading and refreshing the asset tab.
        """
        self._configure_renderer()
        self._assets.gather()
        self._assets.extend(self.renderer.renderer_assets())

    def get_project(self):
        """Get the current project name in order to use this as the asset file
        group.
        """
        project_path = maya.workspace(query=True, fullName=True)
        name = project_path.split('/')[-1]
        # Make lower case
        name = name.lower()
        # Remove any chars that aren't 'a-z', '0-9' or '-'
        name = re.sub(r'\W+', '', name)
        return name

    def get_assets(self):
        """Returns the current asset references for display. Called by the UI
        on loading and refresh.
        """
        self._log.debug("Getting initial assets")
        self._log.debug(str(self._assets.refs))
        return self._assets.refs

    def add_files(self, files, column_layout, scroll_layout):
        """Function called by the 'Add File(s)' button in the UI for adding arbitrary
        file references to the collection to be included with the next job subbmission.
        """
        for f in files:
            self._assets.add_asset(f, self.ui, column_layout, scroll_layout)

    def add_dir(self, dirs, column_layout, scroll_layout):
        """Function called by the 'Add Directory' button in the UI for adding arbitrary
        file references to the collection to be included with the next job subbmission.
        """
        for folder in dirs:
            for root, _, files in os.walk(folder):
                for filename in files:
                    self._assets.add_asset(
                        os.path.join(root, filename), self.ui, column_layout, scroll_layout)

    def upload(self, job_set=None, progress_bar=None, job_id=None, load_plugins=None, os_flavor=None):
        """Upload all the selected assets. Can be initiated as a standalone process
        from the assets tab, or as part of job submission.
        :param job_set: A list of job assets, like the scene file. This is only populated
         if the upload process is part of job submission.
        :param progress_bar: The progress of the current process. This is only populated
         if the upload process is part of job submission.
        :param job_id: The ID of the job being submitted. This is only populated if the
         upload process is part of job submission.
        :param load_plugins: A list of plugins to be added to the pre-render script for
         loading on the server. Only populated if part of a job submission.
        :param os_flavor: The OS flavor of the rendering pool. Only set as part of the job
         submission process.
        """
        asset_data = {}
        try:
            if not job_set:
                progress_bar = ProgressBar(self._log)
                self.ui.disable(False)
                self.ui.upload_button.start()
                self.ui.upload_status("Checking assets...")

            asset_refs = self._collect_assets()
            self._log.debug("Finished collecting, preparing for upload.")
            if job_set:
                self._log.debug("Preparing job specific assets")
                job_assets = [Asset(j, None, self.batch, self._log) for j in job_set]
                path_map, search_paths = self._create_path_map(load_plugins, os_flavor)
                thumb_script = Asset(os.path.join(os.environ['AZUREBATCH_TOOLS'], 'generate_thumbnails.py'),
                                     [], self.batch, self._log)
                workspace = self._create_remote_workspace(os_flavor)
                asset_refs.extend(job_assets)
                asset_refs.extend([path_map, thumb_script, workspace])
                asset_data['search_paths'] = search_paths

            progress_bar.is_cancelled()
            progress_bar.status('Uploading files...')
            progress_bar.max(len(asset_refs))
            self._switch_tab()
            self.ui.disable(False)
            self.ui.upload_button.start()
            payload = self._total_data(asset_refs)
            self.ui.upload_status("Uploading {0}...".format(self._format_size(payload)))
            maya.refresh()
            asset_data['project'] = self.ui.get_project()
            self._upload_all(asset_refs, progress_bar, payload, asset_data['project'])
            if job_set:
                asset_data['path_map'] = path_map.get_url(asset_data['project'])
                asset_data['thumb_script'] = thumb_script.get_url(asset_data['project'])
                asset_data['workspace'] = workspace.get_url(asset_data['project'])
                return asset_data, progress_bar
            else:
                return None

        except CancellationException as exp:
            if job_set:
                raise
            else:
                maya.info(str(exp))
        except Exception as exp:
            if job_set:
                raise
            else:
                maya.error(str(exp))
        finally:
            # If part of job submission, errors and progress bar
            # will be handled back in submission.py
            for index, asset in enumerate(asset_refs):
                asset.restore_label()
            if not job_set:
                progress_bar.end()
            self.ui.upload_button.finish()
            self.ui.disable(True)


class Assets(object):
    """A collection of asset references."""

    def __init__(self, batch):
        self._log = logging.getLogger('AzureBatchMaya')
        self.batch = batch
        self.refs = []
        self.pathmaps = {}
  
    def _search_path(self, ref_path):
        """Validate an asset path and if the file does not exist, attempt
        to resolve it against the system search paths (using the scene file and current
        project) and user specified search paths. If the asset paths contains
        a pattern - resolve this to all applicable files.
        """
        ref_file = os.path.basename(ref_path)
        ref_dir = os.path.dirname(ref_path)
        pattern = ('*' in ref_path or '[0-9]' in ref_path)
        self._log.debug("Searching for asset path: {}".format(ref_path))
        self._log.debug("Checking pattern asset: {}".format(pattern))
        if pattern:
            path_matches = glob.glob(ref_path)
            if path_matches:
                self.pathmaps[ref_dir] = utils.get_remote_file_path(ref_path)
                self._log.debug("Mapping this path {} to {}".format(ref_path, self.pathmaps[ref_dir]))
                self._log.debug("Found matches: {}".format(path_matches))
                return path_matches
        elif os.path.exists(ref_path):
            self.pathmaps[ref_dir] = utils.get_remote_file_path(ref_path)
            self._log.debug("Mapping this path {} to {}".format(ref_path, self.pathmaps[ref_dir]))
            return [ref_path]

        for searchpath in SYS_SEARCHPATHS:
            alt_path = os.path.join(searchpath, ref_file)
            if pattern:
                path_matches = glob.glob(alt_path)
                if path_matches:
                    self.pathmaps[ref_dir] = utils.get_remote_file_path(alt_path)
                    self._log.debug("Mapping this path {} to {}".format(ref_path, self.pathmaps[ref_dir]))
                    self._log.debug("Found matches: {}".format(path_matches))
                    return path_matches
            elif os.path.exists(alt_path):
                self.pathmaps[ref_dir] = utils.get_remote_file_path(alt_path)
                self._log.debug("Mapping this path {} to {}".format(ref_path, self.pathmaps[ref_dir]))
                return [alt_path]

        for searchpath in USR_SEARCHPATHS:
            for _root, _dir, _file in os.walk(searchpath):
                alt_path = os.path.join(_root, ref_file)
                if pattern:
                    path_matches = glob.glob(alt_path)
                    self._log.debug("Found matches: {}".format(path_matches))
                    if path_matches:
                        self.pathmaps[ref_dir] = utils.get_remote_file_path(alt_path)
                        self._log.debug("Mapping this path {} to {}".format(ref_path, self.pathmaps[ref_dir]))
                        return path_matches
                elif os.path.exists(alt_path):
                    self.pathmaps[ref_dir] = utils.get_remote_file_path(alt_path)
                    self._log.debug("Mapping this path {} to {}".format(ref_path, self.pathmaps[ref_dir]))
                    return [alt_path]
        self._log.debug("No matches for reference: {}".format(ref_path))
        return [ref_path]

    def _get_textures(self):
        """Find all texture references in the scene. This generally picks up most
        asset types.
        """
        assets = []
        iter_nodes = maya.dependency_nodes()
        while not iter_nodes.is_done():
            references = iter_nodes.get_references()
            for filepath in references:
                try:
                    checked_paths = self._search_path(filepath)
                    for _path in checked_paths:
                        asset = Asset(_path, assets, self.batch, self._log)
                        if not asset.is_duplicate(assets):
                            assets.append(asset)
                except Exception as exp:
                    self._log.warning("Failed to extract asset file from reference: {0}".format(exp))
                    continue
        self._log.debug("Found {0} external files.".format(len(assets)))
        return assets

    def _get_references(self):
        """Get Maya scene file references as assets."""
        assets = []
        ref_nodes = maya.get_list(references=True)
        references = [maya.reference(r, filename=True, withoutCopyNumber=True) for r in ref_nodes]
        references = set([r for r in references if r])
        for r in references:
            asset = Asset(r, assets, self.batch, self._log)
            if (not asset.is_duplicate(self.refs)):
                assets.append(asset)
        self._log.debug("Found {0} references.".format(len(assets)))
        return assets

    def _get_bifrost_caches(self, assets):
        start = maya.start_frame()
        end = maya.end_frame()
        step = maya.frame_step()
        caches = []
        cache_paths = []
        containers = maya.get_list(type="bifrostContainer")
        for container in containers:
            for cache_type in ['Foam', 'Guide', 'Liquid', 'LiquidMesh', 'Solid']:
                try:
                    enabled = maya.get_attr(container + ".enable{}Cache".format(cache_type))
                except ValueError:
                    continue
                if enabled:
                    cache_name = maya.get_attr(container + ".{}CacheFileName".format(cache_type.lower()))
                    cache_path = maya.get_attr(container + ".{}CachePath".format(cache_type.lower()))
                    cache_paths.append(os.path.join(cache_path, cache_name))
        cache_paths = list(set(cache_paths))
        for cache_path in cache_paths:
            for frame in range(start, end+step, step):
                frame_name = "*.{}.bif".format(str(frame).zfill(4))
                caches.extend(glob.glob(os.path.join(cache_path, "**", frame_name)))
        caches = list(set(caches))
        for cache in caches:
            asset = Asset(cache, assets, self.batch, self._log)
            if not asset.is_duplicate(assets):
                assets.append(asset)

    def _get_caches(self):
        """Gather data caches as assets. TODO: This needs to be tested.
        We generally only want to gather caches relevant to the current
        render frame range or we could end up uploading way too much data.
        """
        assets = []
        cacheFiles = maya.get_list(type="cacheFile")
        for c in cacheFiles:
            c_path = maya.get_attr(c+".cachePath")
            c_name = maya.get_attr(c+".cacheName")

            if c_path and c_name:
                full_path = os.path.join(c_path, c_name)
                path_matches = glob.glob(full_path + "*")
                for cache_path in path_matches:
                    asset = Asset(cache_path, assets, self.batch, self._log)
                    assets.append(asset)

        self._get_bifrost_caches(assets)
        self._log.debug("Found {0} caches.".format(len(assets)))
        return assets

    def gather(self):
        """Parse scene for all asset references. Called on loading and
        refreshing the asset tab.
        """
        self.refs = []
        self.pathmaps = {}
        self.refs.extend(self._get_textures())
        self.refs.extend(self._get_caches())
        self.refs.extend(self._get_references())

    def add_asset(self, file, ui, column_layout, scroll_layout):
        """Add an additional single file to the asset list."""
        self._log.info("Adding file: {0}".format(file))
        asset = Asset(file, self.refs, self.batch, self._log)
        if not asset.is_duplicate(self.refs):
            asset.display(ui, column_layout, scroll_layout)
            self.refs.append(asset)

    def extend(self, more_assets):
        """Add additional assets to the current collection."""
        assets = []
        for f in more_assets:
            try:
                checked_paths = self._search_path(f)
                for _path in checked_paths:
                    asset = Asset(_path, assets, self.batch, self._log)
                    if (not asset.is_duplicate(assets)) and (not asset.is_duplicate(self.refs)):
                        assets.append(asset)
            except Exception as exp:
                self._log.debug("Failed to extend assets: {0}".format(exp))
                continue
        self.refs.extend(assets)

    def collect(self):
        """Compile a list of the asset references that have been selected
        to include with the current job.
        """
        self._log.info("Collecting assets...")
        userfiles = [f for f in self.refs if f.included()]
        self._log.debug("Using {0} external assets.".format(len(userfiles)))
        return userfiles


class Asset(object):
    """Representation of a single asset, managing its file reference,
    display listing and upload of the file.
    """

    def __init__(self, filepath, parent, batch, log=None):
        self.batch = batch
        if not os.path.isabs(filepath):
            filepath = os.path.join(utils.get_root_dir(), filepath)
        self.path = os.path.realpath(os.path.normpath(filepath))
        self.label = "    {0}".format(os.path.basename(self.path))
        self.exists = os.path.exists(self.path)
        self.lastmodified = datetime.fromtimestamp(os.path.getmtime(self.path)) if self.exists else None
        self.note = self.path if self.exists else "Can't find {0}".format(self.path)
        self.parent_list = parent
        self.check_box = None
        self.size = float(os.path.getsize(self.path)) if self.exists else 0
        self.display_text = None
        self.log = log
        if self.exists:
            self.pathmap = {os.path.dirname(self.path): utils.get_remote_file_path(self.path)}
            self.storage_path = utils.get_storage_file_path(self.path)
        else:
            self.pathmap = {}
            self.storage_path = None

    def display(self, ui, layout, scroll):
        """Create the UI elements that will display this asset depending
        on whether the file path has been resolved or not.
        """
        self.frame = ui
        self.scroll_layout = scroll

        if self.exists:
            self.check_box = maya.symbol_check_box(
                value=True, parent=layout,
                onCommand=lambda e: self.include(),
                offCommand=lambda e: self.exclude(),
                annotation="Click to remove asset from submission")
        else:
            self.check_box = maya.symbol_button(
                image="fpe_someBrokenPaths.png", parent=layout,
                command=lambda e: self.search(),
                height=17, annotation="Add search path")
        self.display_text = maya.text(self.label, parent=layout, enable=self.exists, annotation=self.note, align="left")

    def included(self):
        """Returns whether the asset has been selected for inclusion in the upload."""
        if self.check_box and self.exists:
            return bool(maya.symbol_check_box(self.check_box, query=True, value=True))
        else:
            return self.exists

    def include(self):
        """Include this asset in the list for files to be uploaded for submission."""
        if self not in self.parent_list:
            self.parent_list.append(self)
        maya.symbol_check_box(
            self.check_box, edit=True,
            annotation="Click to remove asset from submission")

    def search(self):
        """If a filepath is unresolved, we let the user add an arbitrary search
        path that we can use to attempt to find the asset.
        """
        global USR_SEARCHPATHS
        cap = "Select directory of assets"
        okCap = "Add Search Path"
        new_dir = maya.file_select(fileMode=3, okCaption=okCap, caption=cap)
        if not new_dir:
            return
        USR_SEARCHPATHS.append(new_dir[0])
        self.frame.refresh()

    def exclude(self):
        """Remove this asset from the list of files to be uploaded."""
        try:
            self.parent_list.remove(self)
            maya.symbol_check_box(self.check_box, edit=True, annotation="Click to include asset in submission")
        except ValueError:
            pass

    def delete(self):
        """Remove this asset from the UI display. This is usually done on
        a refresh of the asset tab in order to wipe the UI for repopulating.
        """
        try:
            self.parent_list.remove(self)
        except ValueError:
            pass
        maya.delete_ui(self.check_box, control=True)

    def is_duplicate(self, files):
        """Check whether this file is already represented in the current
        asset list.
        """
        for file_ref in files:
            this_path = self.path.lower() if utils.is_windows() else self.path
            ref_path = file_ref.path.lower() if utils.is_windows() else file_ref.path
            if this_path == ref_path:
                return True
        return False

    def restore_label(self):
        """Restore the original UI display label after the file has been
        uploaded.
        """
        if self.display_text:
            maya.text(self.display_text, edit=True, label=self.label)

    def make_visible(self, index):
        """Attempt to auto-scroll the asset display list so that the progress of
        currently uploading assets remains in view.
        TODO: This needs some work....
        """
        if index == 0:
            while maya.scroll_layout(self.scroll_layout, query=True, scrollAreaValue=True)[0] > 0:
                maya.scroll_layout(self.scroll_layout, edit=True, scrollPage="up")
        elif index >= 4:
            scroll_height = maya.text(self.display_text, query=True, height=True)
            maya.scroll_layout(self.scroll_layout, edit=True, scrollByPixel=("down", scroll_height))
        maya.refresh()

    def get_url(self, project):
        file_name = os.path.basename(self.path)
        return self.batch.file.generate_sas_url(
            project, file_name, remote_path=self.storage_path)

    def upload(self, index, progress_bar, queue, project):
        """Upload this asset file. This is performed outside of Maya's
        main UI thread, therefore any calls to the Maya API must be added to the
        queue to be processed by the main thread or Maya will crash (or at the
        very least behave strangely).
        """
        self.log.debug("Starting asset upload: {}".format(self.path))
        queue.put(progress_bar.is_cancelled)
        if progress_bar.done:
            return
        name = os.path.basename(self.path)
        if self.display_text:
            if index:
                queue.put(lambda: self.make_visible(index))
            queue.put(lambda: maya.text(
                self.display_text, edit=True,
                label="    Uploading 0% {0}".format(name)))
            queue.put(maya.refresh)

        def update(update):
            # Update the % complete in the asset label
            if self.display_text:
                maya.text(self.display_text, edit=True, label="    Uploading {0}% {1}".format(int(update), name))
                maya.refresh()
        uploader = UploadProgress(progress_bar, update, queue, self.log)
        try:
            self.batch.file.upload(
                self.path, project, self.storage_path,
                progress_callback=uploader)
        except Exception as exp:
            queue.put(FileUploadException("Upload failed for {0}: {1}".format(name, exp)))
        else:
            if self.display_text:
                queue.put(lambda: maya.text(
                    self.display_text, edit=True,
                    label="    Uploading 100% {0}".format(name)))
                queue.put(maya.refresh)
        finally:
            self.log.debug("Finished asset upload: {}".format(self.path))
            queue.put(self.size)


class UploadProgress(object):
    """Upload progress callback. Updates progress bar and checks
    for cancellation.
    """

    def __init__(self, prog_bar, cmd, queue, log):
        self.progress = 0
        self.bar = prog_bar
        self.command = cmd
        self.queue = queue
        self.log = log

    def __call__(self, data, total):
        self.queue.put(self.bar.is_cancelled)
        if self.bar.done:
            raise CancellationException("File upload cancelled")
        progress = float(data)/float(total)*100
        self.log.debug(str(progress) + " " + str(self.progress))
        if int(progress) > self.progress:
            self.progress = int(progress)
            self.queue.put(lambda: self.command(progress))
