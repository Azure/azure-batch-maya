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

from api import MayaAPI as maya
import utils


class HistoryUI(object):

    def __init__(self, base, frame):

        self.base = base
        self.label = "  Jobs  "
        self.ready = False

        self.jobs_displayed = []

        with utils.RowLayout(width=360) as layout:
            self.page = layout

            with utils.ColumnLayout(1, col_width=(1,360)) as col:  
                self.total = maya.text(label="", font="boldLabelFont")
                self.paging_display()

            with utils.ScrollLayout(v_scrollbar=3, h_scrollbar=0, width=355, height=478):
 
                with utils.ColumnLayout(1, col_width=(1,345)) as col:
                    if not self.jobs_displayed:

                        self.empty_jobs = maya.text(
                            label="Loading job data...",
                            align='left',
                            font="boldLabelFont")

                    self.jobs_layout = col
                        
            with utils.ColumnLayout(1, col_width=(1,355)) as col:
                maya.button(label="Refresh", command=self.refresh)

        frame.add_tab(self)
        self.is_logged_out()

    @property
    def num_jobs(self):
        maya.text(self.total, query=True, label=True)

    @num_jobs.setter
    def num_jobs(self, value):
        maya.text(self.total, edit=True, label=value)

    @property
    def last_page(self):
        return maya.button(self.next_btn, query=True, enable=True)

    @last_page.setter
    def last_page(self, value):
        maya.button(self.next_btn, edit=True, enable=value)
        maya.button(self.last_btn, edit=True, enable=value)

    @property
    def first_page(self):
        return maya.button(self.prev_btn, query=True, enable=True)

    @first_page.setter
    def first_page(self, value):
        maya.button(self.first_btn, edit=True, enable=value)
        maya.button(self.prev_btn, edit=True, enable=value)

    def is_logged_in(self):
        maya.row_layout(self.page, edit=True, enable=True)

    def is_logged_out(self):
        maya.row_layout(self.page, edit=True, enable=False)
        self.ready = False

    def prepare(self):
        if not self.ready:
            maya.refresh()
            try:
                self.refresh()
                self.is_logged_in()
                self.ready = True

            except Exception as exp:
                maya.error("Error starting Assets UI: {0}".format(exp))
                self.is_logged_out()

        maya.refresh()

    def paging_display(self):
        with utils.ColumnLayout(2, col_width=((1, 180),(2, 180))):

            with utils.ColumnLayout(2, col_width=((1, 85),(2, 85))) as prev:
                self.first_btn = maya.button(label="<<", align="center", command=self.show_first_jobs)
                self.prev_btn = maya.button(label="<", align="center", command=self.show_prev_jobs)

            with utils.ColumnLayout(2, col_width=((1, 85),(2, 85))) as next:
                self.next_btn = maya.button(label=">", align="center", command=self.show_next_jobs)
                self.last_btn = maya.button(label=">>", align="center", command=self.show_last_jobs)


    def refresh(self, *k):
        try:
            maya.delete_ui(self.empty_jobs)
        except RuntimeError:
            pass

        self.base.job_selected(None)
        for i in self.jobs_displayed:
            i.remove()

        self.jobs_displayed = self.base.get_history()
        if not self.jobs_displayed:
            self.empty_jobs = maya.text(label="No jobs to display", parent=self.jobs_layout)
        

    def create_job_entry(self, name, index):
        frame = maya.frame_layout(label=name,
                                  collapsable=True,
                                  collapse=True,
                                  borderStyle='in',
                                  width=345,
                                  visible=True,
                                  parent=self.jobs_layout)

        return BatchAppsJobInfo(self.base, index, frame)

    def show_next_jobs(self, *k):
        self.base.show_next_jobs()
        self.refresh()

    def show_prev_jobs(self, *k):
        self.base.show_prev_jobs()
        self.refresh()

    def show_first_jobs(self, *k):
        self.base.show_first_jobs()
        self.refresh()

    def show_last_jobs(self, *k):
        self.base.show_last_jobs()
        self.refresh()


class BatchAppsJobInfo:

    def __init__(self, base, index, layout):
        
        self.base = base
        self.index = index
        self.layout = layout

        maya.frame_layout(layout,
                          edit=True,
                          collapseCommand=self.on_collapse,
                          expandCommand=self.on_expand)

        self.listbox = maya.col_layout(numberOfColumns=2,
                                       columnWidth=((1, 100),
                                                    (2, 200)),
                                       rowSpacing=((1, 5),),
                                       rowOffset=((1, "top", 5),(1, "bottom", 5),),
                                       parent=self.layout)
        self.content = []


    def set_label(self, value):
        maya.frame_layout(self.layout, edit=True, label=value)

    def set_status(self, value):
        maya.text(self._status, edit=True, label=" {0}".format(value))

    def get_status(self):
        return maya.text(self._status, query=True, label=True).lstrip()

    def set_progress(self, value):
        maya.text(self._progress, edit=True, label=" {0}%".format(value))

    def set_submission(self, value):
        datetime = value.split('T')
        datetime[1] = datetime[1].split('.')[0]
        label = ' '.join(datetime)
        maya.text(self._submission, edit=True, label=" {0}".format(label))

    def set_tasks(self, value):
        maya.text(self._tasks, edit=True, label=" {0}".format(value))

    def set_job(self, value):
        maya.text(self._job, edit=True, label=" {0}".format(value))

    def set_pool(self, value):
        maya.text(self._pool, edit=True, label=" {0}".format(value))

    def on_expand(self):

        self.content.append(maya.text(label=""))
        self.content.append(maya.text(label="Preview:   ", parent=self.listbox, align="right"))

        self._thumbnail = maya.image(parent=self.listbox)
        self.content.append(self._thumbnail)
        
        self._status = self.display_info("Status:   ")
        self._progress = self.display_info("Progress:   ")
        self._submission = self.display_info("Submission time:   ")
        self._tasks = self.display_info("Task Count:   ")
        self._job = self.display_info("Job ID:   ")
        self._pool = self.display_info("Pool:   ")

        with utils.RowLayout(row_spacing=5, col_attach=("both",20), parent=self.layout) as buttons:
            self.button_layout = buttons
            self.content.append(self.button_layout)

            self.base.job_selected(self)
            maya.execute(self.base.get_thumb)  

            self.complete_job() if (self.get_status() == "Complete") else self.incomplete_job()
            self.content.append(maya.text(label="", parent=self.layout))

        maya.refresh()

    def on_collapse(self):
        self.base.job_selected(None)
        maya.parent(self.listbox)
        for element in self.content:
            maya.delete_ui(element, control=True)

        self.content = []

    def collapse(self):
        maya.frame_layout(self.layout, edit=True, collapse=True)
        self.on_collapse()
        maya.refresh()

    def remove(self):
        maya.delete_ui(self.layout, control=True)

    def complete_job(self):
        self.download_button = self.button("Download Output", self.download_output)
        self.cancel_button = None
        return [self.download_output]

    def incomplete_job(self):
        self.download_button = None

        if self.get_status() in ["InProgress", "NotStarted"]:
            self.cancel_button = self.button("Cancel Job", self.cancel_job)
            return [self.cancel_button]
        else:
            return []

    def display_info(self, label):
        self.content.append(maya.text(label=label, parent=self.listbox, align="right"))
        input = maya.text(align="left", label="", parent=self.listbox)
        self.content.append(input)
        return input

    def button(self, label, command):
        return maya.button(label=label,
                           width=150,
                           parent=self.button_layout,
                           align="center",
                           command=command)

    def set_thumbnail(self, thumb, height):
        maya.image(self._thumbnail,
                   edit=True,
                   image=thumb,
                   height=height)

    def change_download_label(self, label):
        maya.button(self.download_button, edit=True, label="{0}".format(label))

    def download_output(self, *args):
        save_file = maya.file_select(fileFilter="Zip Archive (*.zip)",
                                    fileMode=0,
                                    okCaption="Save to file",
                                    caption="Choose an output")
        if save_file is None:
            return

        save_file = os.path.normpath(save_file[0])
        self.base.download_output(save_file)

    def cancel_job(self, *args):
        self.base.cancel_job()