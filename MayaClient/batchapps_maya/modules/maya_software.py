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

from maya import cmds, mel

import os
import sys
import gzip

from default import BatchAppsRenderJob, BatchAppsRenderAssets


class BatchAppsMayaJob(BatchAppsRenderJob):

    def __init__(self):

        self._renderer = "mayaSoftware"
        self.label = "Maya Software"

    def settings(self):
        if self.scene_name == "":
            job_name = "Untitled"

        else:
            job_name = str(os.path.splitext(os.path.basename(self.scene_name))[0])

        self.job_name = self.display_string("Job Name:   ", job_name)

        self.start = self.display_int("Start frame:   ", self.start_frame, edit=True)
        self.end = self.display_int("End frame:   ", self.end_frame, edit=True)
        self.step = self.display_int("Frame step:   ", self.frame_step, edit=True)

    def get_title(self):
        return str(cmds.textField(self.job_name, query=True, text=True))

    def render_enabled(self):
        return True

    def get_jobdata(self):
        if self.scene_name == "":
            raise ValueError("Current Maya scene has not been saved to disk.")
        else:
            return [self.scene_name]

    def get_params(self):
        params = {}

        params["start"] = cmds.intField(self.start, query=True, value=True)
        params["end"] = cmds.intField(self.end, query=True, value=True)
        params["engine"] = "sw"
        params["jobfile"] = os.path.basename(self.scene_name)

        return params

class MayaRenderAssets(BatchAppsRenderAssets):

    assets = {}
    render_engine = "mayaSoftware"

    def renderer_assets(self):
        return self.assets