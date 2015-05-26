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
import logging
import tempfile
import glob
import struct
import random
import string

from api import MayaAPI as maya
from ui_history import HistoryUI

from batchapps import JobManager
from batchapps.exceptions import RestCallException, FileDownloadException



class BatchAppsHistory(object):
    
    def __init__(self, frame, call):

        self._log = logging.getLogger('BatchAppsMaya')
        self._call = call
        self._session = None

        self.manager = None

        self.index = 0
        self.per_call = 5
        self.count = 0
        self.min = True
        self.max = False
               
        self.ui = HistoryUI(self, frame)
        self.jobs = []
        self.selected_job = None

    #def start(self):
    #    self._log.debug("Starting BatchAppsHistory...")
    #    self.ui.refresh()

    def configure(self, session):
        self._session = session
        self.manager = JobManager(self._session.credentials, self._session.config)

    def get_history(self):
        self.jobs = self._call(self.manager.get_jobs, self.index, self.per_call)
        self.count = len(self.manager)

        self.set_num_jobs()
        self.set_min_max()

        display_jobs = []
        for index, job in enumerate(self.jobs):
            display_jobs.append(self.ui.create_job_entry(job.name, index))

        return display_jobs

    def set_num_jobs(self):
        if (self.index + self.per_call) > self.count:
            extra = (self.index + self.per_call) - self.count
            new_range = ((self.index + self.per_call) - extra)

            self.ui.num_jobs =  "{0} - {1} of {2}".format(
                min((self.index + 1), new_range),
                new_range,
                self.count)

        else:

            self.ui.num_jobs = "{0} - {1} of {2}".format(
                min((self.index + 1), self.count),
                (self.index + self.per_call),
                self.count)

    def set_min_max(self):
        self.min = True if self.index < 1 else False

        if (self.count % self.per_call) == 0:
            self.max = (self.index >= (self.count - self.per_call)) or (self.per_call > self.count)

        else:
            self.max = self.index >= (self.count - self.per_call + (self.per_call - (self.count % self.per_call)))

        self.ui.last_page = not self.max
        self.ui.first_page = not self.min

    def show_next_jobs(self):
        self.index = min(self.index + self.per_call, self.count)

    def show_prev_jobs(self):
        self.index = max(self.index - self.per_call, 0)

    def show_first_jobs(self):
        self.index = 0

    def show_last_jobs(self):
        if (self.count % self.per_call) == 0:
            self.index = self.count - self.per_call
        else:
            self.index = self.count - self.per_call + (self.per_call - (self.count % self.per_call))

    def job_selected(self, job_ui):
        if self.selected_job and job_ui:
            self.selected_job.collapse()

        self.selected_job = job_ui

        try:
            if job_ui:
                self._log.info("Collecting job info...")
                job = self.jobs[job_ui.index]
            
                self.selected_job.set_label("loading...")
                loading_thumb = os.path.join(os.environ["BATCHAPPS_ICONS"], "loading_preview.png")
                self.selected_job.set_thumbnail(loading_thumb, 24)
                maya.refresh()

                self._call(job.update)
                self.selected_job.set_status(job.status)
                self.selected_job.set_progress(job.percentage)
                self.selected_job.set_submission(job.time_submitted)
                self.selected_job.set_tasks(job.number_tasks)
                self.selected_job.set_job(job.id)
                self.selected_job.set_pool(job.pool_id)
                self.selected_job.set_label(job.name)

                maya.refresh()
                self._log.info("Updated {0}".format(job.name))

        except Exception as exp:
            self._log.warning("Failed to update job details {0}".format(exp))
            self.selected_job.collapse()

    def temp_name(self, prefix, size=6, chars=string.hexdigits):
        return str(prefix)+ '.' +''.join(random.choice(chars) for x in range(size))+".png"
    
    def get_thumb(self):
        try:
            job = self.jobs[self.selected_job.index]

        except (IndexError, AttributeError):
            self._log.warning("Selected job index does not match jobs list.")

            if not self.selected_job:
                return

            thumb = os.path.join(os.environ["BATCHAPPS_ICONS"], "no_preview.png")
            self.selected_job.set_thumbnail(thumb, 24)
            return

        if job.status == "Complete":
            self._log.info("Getting job thumbail...")
            self.get_job_thumb(job)

        else:
            tasks = self._call(job.get_tasks)
            self._log.info("Job not complete. Getting task thumbnails...")
            self.get_task_thumb(job, tasks)

    def get_task_thumb(self, job, tasks):
        thumb = os.path.join(os.environ["BATCHAPPS_ICONS"], "no_preview.png")

        if len(tasks) < 1:
            self._log.info("No completed tasks")
            self.selected_job.set_thumbnail(thumb, self.get_image_height(thumb))
            maya.refresh()
            return

        tempDir = tempfile.gettempdir()
        for task in reversed(tasks):
            thumb_name = "{0}.{1}.*.png".format(job.id, task.id)
            existing_thumb = glob.glob(os.path.join(tempDir, thumb_name))
            if existing_thumb:
                thumb = existing_thumb[0] 
                break

            try:
                prefix = "{0}.{1}".format(job.id, task.id)
                thumb_file = self.temp_name(prefix)
                thumb = self._call(task.get_thumbnail, tempDir, thumb_file, True)
                break

            except FileDownloadException as exp:
                self._log.info("Couldn't retrieve thumbnail: {0}".format(exp))  
           
        self.selected_job.set_thumbnail(thumb, self.get_image_height(thumb))
        maya.refresh()

    def get_job_thumb(self, job):
        tempDir = tempfile.gettempdir()
        existing_thumb = glob.glob(os.path.join(tempDir, "{0}.*.png".format(job.id)))
        thumb = os.path.join(os.environ["BATCHAPPS_ICONS"], "no_preview.png")

        if existing_thumb:
            thumb = existing_thumb[0] 

        else:
            thumb_file = self.temp_name("{0}.job".format(job.id))
            try:
                thumb = job.get_thumbnail(tempDir, thumb_file, True)

            except (RestCallException, FileDownloadException) as exp:
                self._log.info("Couldn't retrieve thumbnail: {0}".format(exp)) 
                try:
                    os.remove(thumb_file)
                except:
                    pass

        self.selected_job.set_thumbnail(thumb, self.get_image_height(thumb))
        maya.refresh()

    def cancel_job(self):
        try:
            job = self.jobs[self.selected_job.index]
        except (IndexError, AttributeError) as exp:
            self._log.warning("Selected job index does not match jobs list.")
            return

        resp = self._call(job.cancel)
        if not resp:
            self._log.info("Job was not able to be cancelled.")

    def download_output(self, dir):   
        try:
            self.selected_job.change_download_label("Downloading...")
            maya.refresh()

            job = self.jobs[self.selected_job.index]
            self._call(job.get_output, dir, overwrite=True)

        except (IndexError, AttributeError):
            self._log.warning("Selected job index does not match jobs list.")
            if not self.selected_job:
                self.ui.refresh()
                return

        except FileDownloadException as exp:
            self._log.warning("Error downloading output: {0}".format(exp))
        
        self.selected_job.change_download_label("Download Output")
        maya.refresh()

    def get_image_height(self, image):
        y = 120
        with open(image, 'rb') as im:
            im.read(12)
            if im.read(4) == 'IHDR':
                x, y = struct.unpack("!LL", im.read(8))
        return y