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

import os
import sys
import math
import pkgutil
import inspect
import importlib
import logging
import json

from api import MayaAPI as maya
from api import MayaCallbacks as callback

#from exceptions import CancellationException

from ui_submission import SubmissionUI

from exception import CancellationException
import utils

from batchapps import JobManager
from batchapps.exceptions import RestCallException, SessionExpiredException
from default import BatchAppsRenderJob


class BatchAppsSubmission:

    def __init__(self, frame, call):
        
        self._log = logging.getLogger('BatchAppsMaya')
        self._call = call

        self.ui = SubmissionUI(self, frame)
        self.modules = self.collect_modules()
        self.renderer = None
        self.frame = frame

        self.job_manager = None
        self.asset_manager = None
        self.pool_manager = None
        self.env_manager = None

        callback.after_new(self.ui.refresh)
        callback.after_open(self.ui.refresh)


    def start(self, session, assets, pools, env):
        self._log.debug("Starting BatchAppsSubmission...")

        self.job_manager = JobManager(session.credentials, session.config)
        self.asset_manager = assets
        self.pool_manager = pools
        self.env_manager = env

        if self.renderer:
            self.renderer.delete()

        self.configure_renderer()
        self.renderer.display(self.ui.render_module)
        self.ui.submit_enabled(self.renderer.render_enabled())

        self.ui.is_logged_in()
        maya.refresh()
            
    def collect_modules(self):
        self._log.info("Collecting modules...")

        render_modules = []
        module_dir = os.environ['BATCHAPPS_MODULES']
        
        for importer, package_name, _ in pkgutil.iter_modules([module_dir]):
            if package_name == "default":
                continue

            module = importlib.import_module(package_name)
            for name, obj in inspect.getmembers(module, inspect.isclass): 

                if issubclass(obj, BatchAppsRenderJob):
                    render_modules.append(obj())
                    self._log.debug("Appended {0} to render module list.".format(render_modules[-1].label))

        return render_modules

    def configure_renderer(self):
        self._log.info("Configuring renderer...")

        current_renderer = maya.mel("getAttr defaultRenderGlobals.currentRenderer")
        self._log.debug("Current renderer: {0}".format(current_renderer))

        for module in self.modules:

            if not hasattr(module, 'render_engine'):
                self._log.warning("Module {0} has no render engine attribute. Skipping.".format(module))
                continue

            if module.render_engine == str(current_renderer):
                self.renderer = module
                self._log.debug("Configured renderer to {0}".format(self.renderer.render_engine))
                return

        self.renderer = BatchAppsRenderJob()
        self._log.debug("Configured renderer to {0}".format(self.renderer.render_engine))
                
    def refresh_renderer(self, layout):
        self.renderer.delete()
        self.configure_renderer()
        self.renderer.display(layout)
        self.ui.submit_enabled(self.renderer.render_enabled())

    def available_pools(self):
        pools = self.pool_manager.list_pools(lazy=True)
        return pools

    def check_outputs(self):
        cameras = maya.get_list(type="camera")
        render_cams = [maya.get_attr(c + ".renderable") for c in cameras]
        if not any(render_cams):
            raise ValueError("No render camera selected. Please select a render camera and save the scene before submitting.")

        layers = maya.get_list(type="renderLayer")
        render_layers = [maya.get_attr(l + ".renderable") for l in layers]
        if not any(render_layers):
            raise ValueError("No render layers enabled. Please enable a render layer and save the scene before submitting.")

    def configure_environment(self, job, settings):
        job.version = self.env_manager.version
        plugins = self.env_manager.plugins
        env_vars = self.env_manager.environment_variables
        license = self.env_manager.license

        settings["Plugins"] = plugins
        settings["EnvVariables"] = env_vars
        settings.update(license)

        job.settings = json.dumps(settings)

    def submit(self):

        self.renderer.disable(False)
        self.ui.processing(False)
        progress = utils.ProgressBar()
        maya.refresh()

        try:
            self.check_outputs()
            self.ui.submit_status("Checking assets...")
            renderer_data = self.renderer.get_jobdata()
            files, maps, progress = self.asset_manager.upload(renderer_data, progress_bar=progress)
            self.frame.select_tab(2)

            self.ui.submit_status("Setting pool...")
            progress.status("Setting pool...")
            new_job = self.job_manager.create_job(self.renderer.get_title())
            pool_spec = self.ui.get_pool()

            if pool_spec.get(1):
                self._log.info("Using auto-pool.")
                new_job.instances = int(pool_spec[1])

            if pool_spec.get(2):
                self._log.info("Using existing pool.")
                new_job.pool = str(pool_spec[2])

                if new_job.pool == "None":
                    maya.error("No pool selected.")
                    return

            if pool_spec.get(3):
                self._log.info("Creating new pool.")
                new_job.pool = self.pool_manager.create_pool(int(pool_spec[3]))

            new_job.add_file_collection(files)
            self.ui.submit_status("Configuring job...")
            progress.status("Configuring job...")
            new_job.params = self.renderer.get_params()
            self.configure_environment(new_job, maps)
            if progress.is_cancelled():
                raise CancellationException("Job submission cancelled")
                    
            self._log.info("Upload complete. Submitting...")
            self._log.debug(new_job._create_job_message())
            self.ui.submit_status("Submitting...")
            progress.status("Submitting...")
            self._call(new_job.submit)
            
        except CancellationException:
            maya.info("Job submission cancelled")

        except SessionExpiredException:
            pass

        except Exception as exp:
            maya.error(str(exp))

        finally:
            progress.end()
            self.frame.select_tab(2)
            self.renderer.disable(True)
            self.ui.processing(True)



