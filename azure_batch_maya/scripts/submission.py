# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import unicode_literals

import os
import sys
import pkgutil
import inspect
import importlib
import logging
import json
import uuid
import traceback

from azure.batch_extensions import models
from azurebatchmayaapi import MayaAPI as maya
from azurebatchmayaapi import MayaCallbacks as callback

from ui_submission import SubmissionUI
from exception import CancellationException, PoolException
import azurebatchutils as utils
from default import AzureBatchRenderJob


class AzureBatchSubmission(object):
    """Handler for job submission functionality."""

    def __init__(self, index, frame, call):
        """Create new Submission Handler.

        :param index: The UI tab index.
        :param frame: The shared plug-in UI frame.
        :type frame: :class:`.AzureBatchUI`
        :param func call: The shared REST API call wrapper.
        """
        self._log = logging.getLogger('AzureBatchMaya')
        self._call = call
        self._tab_index = index

        self.max_pool_size = 1000
        self.ui = SubmissionUI(self, frame)
        self.modules = self._collect_modules()
        self.renderer = None
        self.frame = frame
        self.asset_manager = None
        self.pool_manager = None
        self.env_manager = None
        self.batch = None

        #callback.after_new(self.ui.refresh)
        #callback.after_open(self.ui.refresh)

    def _collect_modules(self):
        """Collect the renderer-specific submission modules. This is where
        the renderer-specfic job processing is defined.
        """
        self._log.info("Collecting modules...")
        render_modules = []
        module_dir = os.environ['AZUREBATCH_MODULES']
        for importer, package_name, _ in pkgutil.iter_modules([module_dir]):
            if package_name == "default":
                continue
            module = importlib.import_module(package_name)
            for name, obj in inspect.getmembers(module, inspect.isclass): 
                if issubclass(obj, AzureBatchRenderJob):
                    renderer = obj()
                    render_modules.append(renderer)
                    self._log.debug(
                        "Appended {0} to render module list.".format(renderer.label))
        return render_modules

    def _configure_renderer(self):
        """Configure the renderer-specific job processing according
        to the currently selected render engine.
        Called by both the start and refresh functions.
        """
        self._log.info("Configuring renderer...")
        current_renderer = utils.get_current_scene_renderer()
        self._log.debug("Current renderer: {0}".format(current_renderer))

        for module in self.modules:
            if not hasattr(module, 'render_engine'):
                self._log.warning(
                    "Module {0} has no render engine attribute. Skipping.".format(module))
                continue
            if module.render_engine == str(current_renderer):
                self.renderer = module
                self._log.debug("Configured renderer to {0}".format(self.renderer.render_engine))
                return
        self.renderer = AzureBatchRenderJob()
        self._log.debug("Configured renderer to {0}".format(self.renderer.render_engine))

    def _switch_tab(self):
        """Make this tab the currently displayed tab. If this tab is already
        open, this will do nothing.
        """
        self.frame.select_tab(self._tab_index)

    def _check_outputs(self):
        """Check whether at least one of the scene cameras is marked as renderable
        and that at least one layer is a render layer. If not, there will be no
        outputs so we raise an error.
        """
        cameras = maya.get_list(type="camera")
        render_cams = [maya.get_attr(c + ".renderable") for c in cameras]
        if not any(render_cams):
            raise ValueError("No render camera selected. Please select a render "
                             "camera and save the scene before submitting.")
        layers = maya.get_list(type="renderLayer")
        render_layers = [maya.get_attr(l + ".renderable") for l in layers]
        if not any(render_layers):
            raise ValueError("No render layers enabled. Please enable a render "
                             "layer and save the scene before submitting.")

    def _check_plugins(self):
        """Checks through all plug-ins that are currently in use (according to Maya)
        by the scene. We compile a list of those that we both support and should not
        ignore and return for inclusion in the pre-render script plug-in loading.

        TODO: This has been temporarily disabled because some of the plug-ins were
        causing errors in Maya on the render nodes. Need to investigate and add the
        culprits to the ignore list if necessary.
        """
        try:
            with open(os.path.join(os.environ['AZUREBATCH_TOOLS'],
                    "supported_plugins.json"), 'r') as plugins:
                supported_plugins = json.load(plugins)
            with open(os.path.join(os.environ['AZUREBATCH_TOOLS'],
                    "ignored_plugins.json"), 'r') as plugins:
                ignored_plugins = json.load(plugins)
        except EnvironmentError:
            self._log.warning("Unable to load supported plugins")
            return []
        loaded_plugins = maya.plugins(query=True, listPlugins=True)
        unsupported_plugins = [p for p in loaded_plugins \
            if p not in supported_plugins and p not in ignored_plugins]
        if unsupported_plugins:
            warning = ("The following plug-ins are used in the scene, but are not "
                       "yet supported.\nRendering may be affected.\n")
            for plugin in unsupported_plugins:
                warning += plugin + "\n"
            options = ['Continue', 'Cancel']
            answer = maya.confirm(warning, options)
            if answer == options[-1]:
                raise CancellationException("Submission Aborted")
        return []
        #return [p for p in loaded_plugins \
        #    if p in supported_plugins and p not in ignored_plugins]

    def _get_os_flavor(self):
        """Figure out whether the selected pool, or potential pool will use
        either Windows or Linux.
        """
        pool_spec = self.ui.get_pool()
        if pool_spec.get(1):
            return self.env_manager.os_flavor()
        if pool_spec.get(2):
            pool_id = str(pool_spec[2])
            if pool_id == "None":
                raise PoolException("No pool selected.")
            return self.pool_manager.get_pool_os(pool_id)
        if pool_spec.get(3):
            return self.env_manager.os_flavor()

    def _configure_pool(self, job_name):
        """Based on the selected pool option for the job, either deploy a new
        pool, create an auto-pool specification, or simply return the ID of the
        chosen existing pool.

        :param str job_name: The name of the job being submitted. Used for creating
         useful pool names.
        """
        pool_spec = self.ui.get_pool()
        if pool_spec.get(1):
            self._log.info("Using auto-pool.")
            return self.pool_manager.create_auto_pool(pool_spec[1], job_name)
        if pool_spec.get(2):
            self._log.info("Using existing pool.")
            pool_id = str(pool_spec[2])
            if pool_id == "None":
                raise PoolException("No pool selected.")
            return {'poolId' : pool_id}
        if pool_spec.get(3):
            self._log.info("Creating new pool.")
            return self.pool_manager.create_pool(pool_spec[3], job_name)

    def _get_task_container_image(self):
        return self.ui.get_task_container_image()

    def start(self, session, assets, pools, env):
        """Load submission tab after plug-in has been authenticated.

        :param session: Authenticated configuration handler.
        :type session: :class:`.AzureBatchConfig`
        :param assets: Asset handler.
        :type assets: :class:`.AzureBatchAssets`
        :param pools: Pool handler.
        :type pools: :class:`.AzureBatchPools`
        :param env: Render node environment handler.
        :type env: :class:`.AzureBatchEnvironment`
        """
        self._log.debug("Starting AzureBatchSubmission...")
        self.batch = session.batch
        self.asset_manager = assets
        self.pool_manager = pools
        self.env_manager = env
        self.data_path = session.path
        if self.renderer:
            self.renderer.delete()
        self._configure_renderer()
        self.renderer.display(self.ui.render_module)
        self.ui.submit_enabled(self.renderer.render_enabled())
        self.ui.is_logged_in()
        maya.refresh()

    def refresh_renderer(self, layout):
        """Refresh the displayed renderer module for job submission
        settings. The module is completely wiped and re-loaded - this allows
        the user to load a new scene, or swap to a new render engine.
        """
        self.renderer.delete()
        self._configure_renderer()
        self.renderer.display(layout)
        self.ui.submit_enabled(self.renderer.render_enabled())

    def available_pools(self):
        """Retrieve the currently available pools to populate
        the job submission pool selection drop down.
        """
        self.env_manager._get_plugin_licenses()
        required_app_licenses = self.env_manager.get_application_licenses()
        pools = self.pool_manager.list_pools(lazy=True, requiredAppLicenses=required_app_licenses)
        return pools

    def submit(self, watch_job=False, download_dir=None):
        """Submit a new job.

        :param watch_job: Whether to launch the job watcher process once
         the job has submitted.
        :param download_dir: If launching the job watcher, a download directory
         must be specified.
        """
        progress = None
        try:
            pool_os = self._get_os_flavor()
            job_id = "maya-render-{}".format(uuid.uuid4())
            container_image = self._get_task_container_image()
            self.renderer.disable(False)
            progress = utils.ProgressBar(self._log)
            maya.refresh()

            mayaVersion = maya.about(version=True)
            if mayaVersion != "2017" and mayaVersion != "2018":
                raise Exception("Unrecognized mayaVersion \"{}\", 2017 and 2018 are supported".format(mayaVersion))

            batch_parameters = {'id': job_id}
            batch_parameters['displayName'] = self.renderer.get_title()
            batch_parameters['metadata'] =  [{"name": "JobType", "value": "Maya"}]
            template_file = utils.build_template_filename(self.renderer.render_engine, mayaVersion, pool_os.value.lower(), container_image)

            batch_parameters['applicationTemplateInfo'] = {'filePath': template_file}
            application_params = {}
            batch_parameters['applicationTemplateInfo']['parameters'] = application_params

            self._check_outputs()
            plugins = self._check_plugins()
            application_params['outputs'] = job_id

            self.ui.submit_status("Checking assets...")
            scene_file, renderer_data = self.renderer.get_jobdata()
            application_params['sceneFile'] = utils.format_scene_path(scene_file, pool_os)
            job_assets, progress = self.asset_manager.upload(
                renderer_data, progress, job_id, plugins, pool_os)

            application_params['projectData'] = job_assets['project']
            application_params['assetScript'] = job_assets['path_map']
            application_params['thumbScript'] = job_assets['thumb_script']
            application_params['workspace'] = job_assets['workspace']
            application_params['storageURL'] = self.asset_manager.generate_sas_token(job_assets['project'])

            if container_image:
                application_params['taskContainerImageName'] = container_image

            self._switch_tab()

            self.ui.submit_status("Configuring job...")
            progress.status("Configuring job...")
            job_params = self.renderer.get_params()
            application_params.update(job_params)

            self.ui.submit_status("Setting pool...")
            progress.status("Setting pool...")
            pool = self._configure_pool(self.renderer.get_title())
            batch_parameters['poolInfo'] = pool
            batch_parameters['commonEnvironmentSettings'] = self.env_manager.get_environment_settings()

            self.ui.submit_status("Final renderer configuration...")
            self.renderer.final_setup(batch_parameters, job_assets)
            
            self._log.debug(json.dumps(batch_parameters))
            new_job = self.batch.job.jobparameter_from_json(batch_parameters)
            progress.is_cancelled()
            self.ui.submit_status("Submitting...")
            progress.status("Submitting...")
            self._log.debug("Submitting using {} threads.".format(self.batch.threads))
            self._call(self.batch.job.add, new_job)
            maya.info("Job submitted successfully")

            if watch_job:
                utils.JobWatcher(new_job.id, self.data_path, download_dir)
        except CancellationException:
            maya.info("Job submission cancelled")
        except Exception as exp:
            self._log.error(str(exp))
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self._log.debug(''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
            maya.error(str(exp))
        finally:
            if progress:
                progress.end()
            self._switch_tab()
            self.renderer.disable(True)
