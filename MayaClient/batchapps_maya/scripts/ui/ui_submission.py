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
import utils

from api import MayaAPI as maya


class SubmissionUI(object):

    def __init__(self, base, frame):

        self.base = base
        self.label = " Submit "

        with utils.RowLayout(width=360) as layout:
            self.page = layout 

            with utils.ScrollLayout(height=497, parent=self.page) as col:
                box_label = "Pool Settings"

                with utils.FrameLayout(label=box_label, width=360, collapsable=True, parent=col) as box:
                
                    self.pool_settings = maya.col_layout(
                        numberOfColumns=2,
                        columnWidth=((1, 80),
                                    (2, 200)),
                        parent=box,
                        rowSpacing=(1, 10),
                        rowOffset=((1, "top", 20),
                                    (2, "bottom", 20)))

                    maya.text(label="Pools:   ", align="right")
                    self.select_pool_type = maya.radio_group(
                        labelArray3=("Auto provision a pool for this job",
                                     "Reuse an existing persistent pool",
                                     "Create a new persistent pool"),
                        numberOfRadioButtons=3,
                        select=1,
                        vertical=True,
                        onCommand1=self.set_pool_instances,
                        onCommand2=self.set_pool_reuse,
                        onCommand3=self.set_pool_instances)

                    self.pool_text = maya.text(label="Instances:   ", align="right")
                    self.control = maya.int_slider(
                        field=True, value=3,
                        minValue=1,
                        maxValue=1000,
                        fieldMinValue=1,
                        fieldMaxValue=1000,
                        annotation="Number of instances in pool")

                box_label = "Render Settings"
                with utils.FrameLayout(label=box_label, width=360, collapsable=True, parent=col) as box:
                    self.render_module = box

            with utils.ColumnLayout(1, col_width=(1,355)) as col:
                self.submit_button = maya.button(label="Submit Job", command=self.submit)
                self.refresh_button = maya.button(label="Refresh", command=self.refresh)

        frame.add_tab(self)

    def is_logged_in(self):
        maya.row_layout(self.page, edit=True, enable=True)

    def is_logged_out(self):
        maya.row_layout(self.page, edit=True, enable=False)

    def prepare(self):
        pass

    def refresh(self, *k):
        self.base.refresh_renderer(self.render_module)
        maya.refresh()

    def processing(self, enabled):
        if enabled:
            maya.button(self.submit_button, edit=True, label="Submit Job", enable=True)
            maya.button(self.refresh_button, edit=True, enable=True)
        else:
            maya.button(self.submit_button, edit=True, label="Submitting...", enable=False)
            maya.button(self.refresh_button, edit=True, enable=False)

    def submit(self, *k):
        self.base.submit()

    def submit_enabled(self, enable):
        maya.button(self.submit_button, edit=True, enable=enable)

    def get_pool(self):
        pool_type = maya.radio_group(self.select_pool_type, query=True, select=True)
        if pool_type == 2:
            details = str(maya.text_field(self.control, query=True, text=True))
        else:
            details = int(maya.int_slider(self.control, query=True, value=True))
        return {pool_type: details}

    def set_pool_instances(self, *k):
        maya.delete_ui(self.pool_text)
        maya.delete_ui(self.control)

        self.pool_text = maya.text(
            label="Instances:   ",
            align="right",
            parent=self.pool_settings)

        self.control = maya.int_slider(
            field=True,
            value=3,
            minValue=1,
            maxValue=1000,
            fieldMinValue=1,
            fieldMaxValue=1000,
            parent=self.pool_settings,
            annotation="Number of instances in pool")

    def set_pool_reuse(self, *k):
        maya.delete_ui(self.pool_text)
        maya.delete_ui(self.control)

        self.pool_text = maya.text(
            label="Pool ID:   ",
            align="right",
            parent=self.pool_settings)

        self.control = maya.text_field(
            parent=self.pool_settings,
            annotation="Use an existing persistent pool ID",
            editable=True)

