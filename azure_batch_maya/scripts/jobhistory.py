# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import logging
import tempfile
import glob
import struct
import random
import string
import shutil
import re

from api import MayaAPI as maya
from ui_jobhistory import JobHistoryUI

import azure.batch as batch


class AzureBatchJobHistory(object):
    """Handler for job display functionality."""
    
    def __init__(self, index, frame, call):
        """Create new job history Handler.

        :param index: The UI tab index.
        :param frame: The shared plug-in UI frame.
        :type frame: :class:`.AzureBatchUI`
        :param func call: The shared REST API call wrapper.
        """
        self._log = logging.getLogger('AzureBatchMaya')
        self._call = call
        self._session = None
        self._tab_index = index
        self.batch = None
        self.index = 0
        self.jobs_per_page = 5
        self.count = 0
        self.min = True
        self.max = False
        self.ui = JobHistoryUI(self, frame)
        self.all_jobs = []
        self.jobs = []
        self.selected_job = None

    def _get_image_height(self, image):
        """Get the pixel height of the job thumbnail to display.
        Note: This function only works under Python 2.7
        """
        # The first 8 bytes of data are the PNG signature, the next 4
        # are the type field of the first chunk (which we don't need).
        png_signature_bytes = 12
        # The IHDR header is always the first chunk in a valid PNG image
        png_header = 'IHDR'
        # X and Y image dimensions are the first 8 bytes of the IDHR chunk
        dimensions_bytes = 8
        # 120 pixels is the default height of a thumbnail image
        y = 120
        # Byte order = network (!), format = unsigned long (L)
        excepted_byte_format = '!LL'
        with open(image, 'rb') as im:
            png_signature = im.read(png_signature_bytes)
            valid_png = im.read(len(png_header)) == png_header
            if valid_png:
                x, y = struct.unpack(excepted_byte_format, im.read(dimensions_bytes))
        return y

    def _download_thumbnail(self, job, thumbs):
        """Download a preview thumbnail for the selected job.
        Only certain output formats are supported. If the thumbnail doesn't
        exist then we display the default 'no preview' image.
        TODO: Remove direct storage reference to use batch.download.

        :param job: The selected job object.
        :param thumbs: A list of thumbnail images available for this job.
        """
        thumb = os.path.join(os.environ["AZUREBATCH_ICONS"], "no_preview.png")
        if len(thumbs) < 1:
            self._log.info("No thumbnails retrieved")
            self.selected_job.set_thumbnail(thumb, self._get_image_height(thumb))
            maya.refresh()
            return
        try:
            temp_dir = os.path.join(tempfile.gettempdir(), job.id)
            if not os.path.isdir(temp_dir):
                os.mkdir(temp_dir)
        except Exception as exp:
            self._log.warning(exp)
            self.selected_job.set_thumbnail(thumb, self._get_image_height(thumb))
            maya.refresh()
            return
        thumb_path = os.path.normpath(os.path.join(temp_dir, os.path.basename(thumbs[-1])))
        self._log.debug("Thumbnail path: {}".format(thumb_path))
        try:
            if not os.path.isfile(thumb_path):
                self._log.info("Downloading task thumbnail: {}".format(thumbs[-1]))
                self.storage.get_blob_to_path('fgrp-' + job.id, thumbs[-1], thumb_path)
                self._log.info("    thumbnail download successful.\n")
        except Exception as exp:
            self._log.warning(exp)
            self.selected_job.set_thumbnail(thumb, self._get_image_height(thumb))
            maya.refresh()
            return
        self.selected_job.set_thumbnail(thumb_path, self._get_image_height(thumb_path))
        maya.refresh()

    def _set_num_jobs(self):
        """Calculate the paging progress label, including which page
        is currently displayed out of how many.
        """
        if (self.index + self.jobs_per_page) > self.count:
            extra = (self.index + self.jobs_per_page) - self.count
            new_range = ((self.index + self.jobs_per_page) - extra)
            self.ui.num_jobs =  "{0} - {1} of {2}".format(
                min((self.index + 1), new_range), new_range, self.count)
        else:
            self.ui.num_jobs = "{0} - {1} of {2}".format(
                min((self.index + 1), self.count), (self.index + self.jobs_per_page), self.count)

    def _set_min_max(self):
        """Determine whether we are currently displaying the first or
        last page, so that the forward and back buttons can be disabled
        accordingly.
        """
        self.min = True if self.index < 1 else False
        if (self.count % self.jobs_per_page) == 0:
            self.max = (self.index >= (self.count - self.jobs_per_page)) or (self.jobs_per_page > self.count)
        else:
            self.max = self.index >= (self.count - self.jobs_per_page + (self.jobs_per_page - (self.count % self.jobs_per_page)))
        self.ui.last_page = not self.max
        self.ui.first_page = not self.min

    def configure(self, session):
        """Populate the Batch client for the current sessions of the job history tab.
        Called on successful authentication.
        """
        self._session = session
        self.batch = self._session.batch
        self.storage = self._session.storage

    def selected_job_id(self):
        """Retrieves the ID of the currently selected job."""
        return self.jobs[self.selected_job.index].id

    def get_data_dir(self):
        """Get the path of the plugin configuration file.
        This is used for configuring the job watcher if it's launched.
        """
        return self._session.path

    def get_history(self):
        """Retrieve the jobs run in the Batch account.
        We filter for only Maya jobs.
        """
        self.all_jobs = [j for j in self._call(self.batch.job.list) \
            if j.metadata and any([m for m in j.metadata if m.name=='JobType' and m.value.startswith('Maya')])]
        self.all_jobs.sort(key=lambda x: x.creation_time, reverse=True)
        self.count = len(self.all_jobs)
        return self.show_jobs()

    def show_jobs(self):
        """Display the current page of jobs."""
        self.jobs = self.all_jobs[self.index:self.index + self.jobs_per_page]
        self._set_num_jobs()
        self._set_min_max()
        display_jobs = []
        for index, job in enumerate(self.jobs):
            display_jobs.append(self.ui.create_job_entry(job.display_name, index))
        return display_jobs

    def show_next_jobs(self):
        """Show the next page of jobs."""
        self.index = min(self.index + self.jobs_per_page, self.count)

    def show_prev_jobs(self):
        """Show the previous page of jobs."""
        self.index = max(self.index - self.jobs_per_page, 0)

    def show_first_jobs(self):
        """Return to the first page of jobs (most recently submitted)."""
        self.index = 0

    def show_last_jobs(self):
        """Skip to the last page of jobs (first ones submitted)."""
        if (self.count % self.jobs_per_page) == 0:
            self.index = self.count - self.jobs_per_page
        else:
            self.index = self.count - self.jobs_per_page + \
                (self.jobs_per_page - (self.count % self.jobs_per_page))

    def job_selected(self, job_ui):
        """A job has been selected, so its details need to be retrieved
        and displayed. This is also called when a job entry has been
        refreshed.
        """
        if self.selected_job and job_ui:
            self.selected_job.collapse()
        self.selected_job = job_ui
        if job_ui:
            self.update_job(job_ui.index)

    def update_job(self, index):
        """Get the latest details on a specified job.
        Also attempts to find a latest thumbnail to display.
        :param int index: The index of the job displayed on the page
         that is currently selected.
        """
        try:
            self._log.info("Collecting job info...")
            job = self.jobs[index]
            self.selected_job.set_label("loading...")
            loading_thumb = os.path.join(os.environ["AZUREBATCH_ICONS"], "loading_preview.png")
            self.selected_job.set_thumbnail(loading_thumb, 24)
            maya.refresh()
            job = self._call(self.batch.job.get, job.id)
            self.selected_job.set_status('loading...')
            self.selected_job.set_progress('loading...')
            self.selected_job.set_tasks('loading...')
            self.selected_job.set_submission(job.creation_time.isoformat())
            self.selected_job.set_job(job.id)
            self.selected_job.set_pool(job.pool_info.pool_id)
            self.selected_job.set_label(job.display_name)
            maya.refresh()
            self._log.info("Updated {0}".format(job.display_name))
        except Exception as exp:
            self._log.warning("Failed to update job details {0}".format(exp))
            self.ui.refresh()

    def load_tasks(self):
        """Get a list of tasks associated with the job."""
        try:
            job = self.jobs[self.selected_job.index]
        except (IndexError, AttributeError):
            self._log.warning("Selected job index does not match jobs list.")
            if not self.selected_job:
                return
            self.selected_job.set_status('unknown')
            self.selected_job.set_progress('unknown')
            self.selected_job.set_tasks('unknown')
            return
        try:
            tasks = list(self._call(self.batch.task.list, job.id))
            completed_tasks = [t for t in tasks if t.state == batch.models.TaskState.completed]
            errored_tasks = [t for t in completed_tasks if t.execution_info.exit_code != 0]
            state = job.state.value
            if len(tasks) == 0:
                percentage = 0
                state = "Pending"
            else:
                percentage = (100 * len(completed_tasks)) / (len(tasks))
            self.selected_job.set_status(state)
            self.selected_job.set_progress(str(percentage)+'%')
            self.selected_job.set_tasks(len(tasks))
            maya.refresh()
        except Exception as exp:
            self._log.warning("Failed to update job details {0}".format(exp))
            self.ui.refresh()

    def get_thumbnail(self):
        """Check job outputs of the currently selected job to find
        any available thumbnails.
        TODO: Remove direct use of storage and replace with batch.download.
        """
        try:
            job = self.jobs[self.selected_job.index]
        except (IndexError, AttributeError):
            self._log.warning("Selected job index does not match jobs list.")
            if not self.selected_job:
                return
            thumb = os.path.join(os.environ["AZUREBATCH_ICONS"], "no_preview.png")
            self.selected_job.set_thumbnail(thumb, 24)
            return
        try:
            blobs = self.storage.list_blobs('fgrp-' + job.id, prefix="thumbs/") # TODO
        except Exception as exp:
            self._log.warning(exp)
            blobs = []
        thumbs = sorted([b.name for b in blobs])
        self._download_thumbnail(job, thumbs)

    def cancel_job(self):
        """Cancel (terminate) the currently selected job."""
        try:
            job = self.jobs[self.selected_job.index]
            self._call(self.batch.job.terminate, job.id)
            self.update_job(self.selected_job.index)
            maya.execute(self.load_tasks)
            maya.execute(self.get_thumbnail)
            maya.refresh()
        except (IndexError, AttributeError) as exp:
            self._log.warning("Selected job index does not match jobs list.")
        except Exception: #TODO get real exception
            self._log.info("Job was not able to be cancelled.")

    def delete_job(self):
        """Delete the currently selected job.
        TODO: We should also delete the output file group from storage.
        """
        try:
            job = self.jobs[self.selected_job.index]
            self._call(self.batch.job.delete, job.id)
            self.update_job(self.selected_job.index)
            maya.execute(self.load_tasks)
            maya.execute(self.get_thumbnail)
            maya.refresh()
        except (IndexError, AttributeError) as exp:
            self._log.warning("Selected job index does not match jobs list.")