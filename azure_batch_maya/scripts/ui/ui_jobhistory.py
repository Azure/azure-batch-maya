# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import webbrowser

from api import MayaAPI as maya
import utils


class JobHistoryUI(object):
    """Class to create the 'Jobs' tab in the plug-in UI"""

    def __init__(self, base, frame):
        """Create 'Jobs' tab and add to UI frame.

        :param base: The base class for handling jobs monitoring functionality.
        :type base: :class:`.AzureBatchJobHistory`
        :param frame: The shared plug-in UI frame.
        :type frame: :class:`.AzureBatchUI`
        """
        self.base = base
        self.label = " Jobs "
        self.ready = False
        self.jobs_displayed = []
        self.page = maya.form_layout(enableBackground=True)

        with utils.Row(1, 1, 360, "center") as lbl:
            self.total = maya.text(label="", font="boldLabelFont")
        self.paging_display()
        with utils.ScrollLayout(
            v_scrollbar=3, h_scrollbar=0, height=478) as scroll:
            with utils.RowLayout(row_spacing=20) as sublayout:
                if not self.jobs_displayed:
                    self.empty_jobs = maya.text(
                        label="Loading job data...",
                        align='left',
                        font="boldLabelFont")
                self.jobs_layout = sublayout

        with utils.Row(1, 1, 355, "center", (1,"bottom",0)) as btn:             
            self.refresh_button = utils.ProcButton(
                "Refresh", "Refreshing...", self.refresh)
        maya.form_layout(
            self.page, edit=True,
            attachForm=[(lbl, 'top', 0), (lbl, 'left', 5),
                        (lbl, 'right', 5),
                        (self.first_btn, 'left', 5),
                        (self.last_btn, 'right', 5),
                        (scroll, 'left', 5), (scroll, 'right', 5),
                        (btn, 'bottom', 5), (btn, 'left', 0),
                        (btn, 'right', 0)],
            attachControl=[(self.first_btn,"top",5, lbl),
                           (self.prev_btn,"top",5, lbl),
                           (self.last_btn,"top",5, lbl),
                           (self.next_btn,"top",5, lbl),
                           (scroll,"top",5, self.first_btn),
                           (scroll,"top",5, self.next_btn),
                           (scroll,"top",5, self.prev_btn),
                           (scroll,"top",5, self.last_btn),
                           (scroll, "bottom", 5, btn)],
            attachPosition=[(lbl, 'top', 5, 0),
                            (self.first_btn, 'right', 5, 25),
                            (self.prev_btn, 'left', 5, 25),
                            (self.prev_btn, 'right', 5, 50),
                            (self.next_btn, 'right', 5, 75),
                            (self.next_btn, 'left', 5, 50),
                            (self.last_btn, 'left', 5, 75),])
        frame.add_tab(self)
        self.is_logged_out()

    @property
    def num_jobs(self):
        """Total number of jobs. Retrieves contents of label."""
        return maya.text(self.total, query=True, label=True)

    @num_jobs.setter
    def num_jobs(self, value):
        """Total number of jobs. Sets contents of label."""
        maya.text(self.total, edit=True, label=value)

    @property
    def last_page(self):
        """Whether the tab is displaying the last page of jobs.
        Retrieves status of paging buttons.
        """
        return maya.button(self.next_btn, query=True, enable=True)

    @last_page.setter
    def last_page(self, value):
        """Whether the tab is displaying the last page of jobs.
        Sets status of paging buttons.
        """
        maya.button(self.next_btn, edit=True, enable=value)
        maya.button(self.last_btn, edit=True, enable=value)

    @property
    def first_page(self):
        """Whether the tab is displaying the first page of jobs.
        Retrieves status of paging buttons.
        """
        return maya.button(self.prev_btn, query=True, enable=True)

    @first_page.setter
    def first_page(self, value):
        """Whether the tab is displaying the first page of jobs.
        Sets status of paging buttons.
        """
        maya.button(self.first_btn, edit=True, enable=value)
        maya.button(self.prev_btn, edit=True, enable=value)

    def is_logged_in(self):
        """Called when the plug-in is authenticated. Enables UI."""
        maya.form_layout(self.page, edit=True, enable=True)

    def is_logged_out(self):
        """Called when the plug-in is logged out. Disables UI and resets
        whether that tab has been loaded for the first time.
        """
        maya.form_layout(self.page, edit=True, enable=False)
        self.ready = False

    def prepare(self):
        """Called when the tab is loaded (clicked into) for the first time.
        Initiates the downloading of job details based on the selected page.
        Once loaded, remains so for the rest of the plug-in session unless
        logged out or manually refreshed.

        If loading the UI fails, the tab returns to a logged-out state.
        """
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
        """Display the buttons for controlling the job paging."""
        self.first_btn = maya.button(
            label="<<", align="center", command=self.show_first_jobs)
        self.prev_btn = maya.button(
            label="<", align="center", command=self.show_prev_jobs)
        self.next_btn = maya.button(
            label=">", align="center", command=self.show_next_jobs)
        self.last_btn = maya.button(
            label=">>", align="center", command=self.show_last_jobs)

    def reload(self, *args):
        """Refresh Jobs tab. Command for refresh_button.
        Remove all existing UI elements and job details and re-build
        from scratch. This is also called to populate 
        the tab for the first time.
        """
        self.refresh_button.start()
        maya.delete_ui(self.empty_jobs)
        self.base.job_selected(None)
        for i in self.jobs_displayed:
            i.remove()
        self.jobs_displayed = self.base.show_jobs()
        if not self.jobs_displayed:
            self.empty_jobs = maya.text(
                label="No jobs to display", parent=self.jobs_layout)
        self.refresh_button.finish()

    def refresh(self, *args):
        """Refresh Jobs tab. Command for refresh_button.
        Remove all existing UI elements and job details and re-build
        from scratch. This is also called to populate 
        the tab for the first time.
        """
        self.refresh_button.start()
        maya.delete_ui(self.empty_jobs)

        self.base.job_selected(None)
        for i in self.jobs_displayed:
            i.remove()
        self.jobs_displayed = self.base.get_history()
        if not self.jobs_displayed:
            self.empty_jobs = maya.text(
                label="No jobs to display", parent=self.jobs_layout)
        self.refresh_button.finish()
        
    def disable(self, enabled):
        """Disable the tab from user interaction. Used during long running
        processes like refreshing the job data, and when plug-in is
        unauthenticated.

        :param bool enabled: Whether to enable the display. False will
         disable the display.
        """
        maya.form_layout(self.page, edit=True, enable=enabled)

    def create_job_entry(self, name, index):
        """Create new dropdown frame to represent a job entry.
        :returns: A :class:`.AzureBatchJobInfo` object.
        """
        frame = maya.frame_layout(label=name,
                                  collapsable=True,
                                  collapse=True,
                                  visible=True,
                                  parent=self.jobs_layout)
        return AzureBatchJobInfo(self.base, index, frame)

    def show_next_jobs(self, *args):
        """Display next set of jobs. Command for next_btn."""
        self.base.show_next_jobs()
        self.reload()

    def show_prev_jobs(self, *args):
        """Display previous set of jobs. Command for prev_btn."""
        self.base.show_prev_jobs()
        self.reload()

    def show_first_jobs(self, *args):
        """Display first jobs. Command for first_btn."""
        self.base.show_first_jobs()
        self.reload()

    def show_last_jobs(self, *args):
        """Display last jobs. Command for last_btn."""
        self.base.show_last_jobs()
        self.reload()


class AzureBatchJobInfo(object):
    """Class to represent a single job reference."""

    def __init__(self, base, index, layout):
        """Create a new job reference.

        :param base: The base class for handling jobs monitoring functionality.
        :type base: :class:`.AzureBatchJobHistory`
        :param int index: The index of where this reference is displayed on
         the current page.
        :param layout: The layout on which the job details will be displayed.
        :type layout: :class:`.utils.FrameLayout`
        """
        self.base = base
        self.index = index
        self.layout = layout
        self.data_path = self.base.get_data_dir()
        self.selected_dir = utils.get_default_output_path()
        maya.frame_layout(
            layout,
            edit=True,
            collapseCommand=self.on_collapse,
            expandCommand=self.on_expand)
        self.job_details = maya.form_layout(parent=self.layout)
        maya.parent()
        self.content = []
        self.url = ""

    def set_label(self, value):
        """Set the label for the job frame layout.
        :param str value: The string to display as label.
        """
        maya.frame_layout(self.layout, edit=True, label=value)

    def set_status(self, value):
        """Set the buttons availability depending on the job status.
        :param str value: The status of the job.
        """
        maya.text(self._status, edit=True, label=" {0}".format(value))
        maya.icon_button(self.refresh_button, edit=True, enable=True)
        maya.icon_button(self.view_button, edit=True, enable=True)
        maya.icon_button(self.watch_button, edit=True, enable=True)
        maya.icon_button(self.cancel_button, edit=True, enable=(
            value in ["active", "enabling"]))
        maya.icon_button(self.delete_button, edit=True, enable=(
            value=='completed'))

    def get_status(self):
        """Get the status of the job."""
        return maya.text(self._status, query=True, label=True).lstrip()

    def set_progress(self, value):
        """Set the label for progress complete.
        :param int value: The percent complete.
        """
        maya.text(self._progress, edit=True, label=" {0}%".format(value))

    def set_submission(self, value):
        """Set the label for date/time submitted.
        :param str value: The datetime string to format.
        """
        datetime = value.split('T')
        datetime[1] = datetime[1].split('.')[0]
        label = ' '.join(datetime)
        maya.text(self._submission, edit=True, label=" {0}".format(label))

    def set_tasks(self, value):
        """Set the label for number of tasks in the job.
        :param int value: The number of tasks.
        """
        maya.text(self._tasks, edit=True, label=" {0}".format(value))

    def set_job(self, value):
        """Set the label for the job ID, and format the portal URL reference
        for the job with this ID.
        Except that with the current portal we have no way to directly link to a job.
        :param str value: The job ID.
        """
        maya.text_field(self._job, edit=True, text=value)
        self.url = "https://portal.azure.com"

    def set_pool(self, value):
        """Set the label for the pool ID that this job ran on.
        :param str value: The pool ID.
        """
        maya.text_field(self._pool, edit=True, text=value)

    def open_portal(self, *args):
        """Open the portal in a web browser to the details page
        for this job. Command for view_button
        """
        webbrowser.open(self.url, 2, True)

    def on_expand(self):
        """Command for the expanding of the job reference frame layout.
        Loads latest details for the specified job and populates UI.
        """
        with utils.Row(2, 2, (100,220), parent=self.job_details) as row:
            self.content.append(row)
            self.content.append(maya.text(label=""))
            self._thumbnail = maya.image()
            self.content.append(self._thumbnail)
        self._status, st_row = self.display_info("Status:   ")
        self._progress, pr_row = self.display_info("Progress:   ")
        self._submission, sb_row = self.display_info("Submitted:   ")
        self._tasks, tk_row = self.display_info("Task Count:   ")
        self._job, jb_row = self.display_data("Job ID:   ")
        self._pool, pl_row = self.display_data("Pool:   ")
        self._dir, dr_row = self.display_watcher()
        self.refresh_button = self.display_button(
            "btn_refresh.png", self.refresh, "Refresh")
        self.view_button = self.display_button(
            "btn_portal.png", self.open_portal,
            "View this job in the portal")
        self.watch_button = self.display_button(
            "btn_background.png", self.start_watcher,
            "Watch this job in the background")
        self.cancel_button = self.display_button(
            "btn_cancel.png", self.cancel_job, "Cancel this job")
        self.delete_button = self.display_button(
            "btn_delete.png",self.delete_job, "Delete job")
        maya.form_layout(
            self.job_details, edit=True,
            attachForm=[(row,"top",5), (row,"left",5), (row,"right",5),
                        (st_row,"left",5), (st_row,"right",5),
                        (pr_row,"left",5), (pr_row,"right",5),
                        (sb_row,"left",5), (sb_row,"right",5),
                        (tk_row,"left",5), (tk_row,"right",5),
                        (jb_row,"left",5), (jb_row,"right",5),
                        (pl_row,"left",5), (pl_row,"right",5),
                        (dr_row,"left",5), (dr_row,"right",5),
                        (self.refresh_button,"left",5),
                        (self.delete_button,"right",5),
                        (self.refresh_button,"bottom",5),
                        (self.view_button,"bottom",5),
                        (self.watch_button,"bottom",5),
                        (self.cancel_button,"bottom",5),
                        (self.delete_button,"bottom",5)],
           attachControl=[(st_row,"top",5, row),
                          (pr_row,"top",5, st_row),
                          (sb_row,"top",5, pr_row),
                          (tk_row,"top",5, sb_row),
                          (jb_row,"top",5, tk_row),
                          (pl_row,"top",5, jb_row),
                          (dr_row,"top",5, pl_row),
                          (self.refresh_button,"top",5, dr_row),
                          (self.view_button,"top",5, dr_row),
                          (self.watch_button,"top",5, dr_row),
                          (self.cancel_button,"top",5, dr_row),
                          (self.delete_button, "top", 5, dr_row)],
            attachPosition=[(self.refresh_button, 'right', 5, 20),
                            (self.view_button, 'left', 5, 20),
                            (self.view_button, 'right', 5, 40),
                            (self.watch_button, 'right', 5, 60),
                            (self.watch_button, 'left', 5, 40),
                            (self.cancel_button, 'left', 5, 60),
                            (self.cancel_button, 'right', 5, 80),
                            (self.delete_button, 'left', 5, 80)])
        self.base.job_selected(self)
        maya.execute(self.base.get_thumbnail)  
        maya.refresh()

    def on_collapse(self):
        """Command for the collapsing of the job reference frame layout.
        Deletes all UI elements and resets currently selected job.
        This is called automatically when the user collapses the UI layout,
        or programmatically from the :func:`collapse` function.
        """
        self.base.job_selected(None)
        maya.parent(self.job_details)
        for element in self.content:
            maya.delete_ui(element, control=True)
        self.content = []

    def collapse(self):
        """Collapse the job frame. Initiates the on_collapse sequence."""
        maya.frame_layout(self.layout, edit=True, collapse=True)
        self.on_collapse()
        maya.refresh()

    def remove(self):
        """Delete the job reference frame layout."""
        maya.delete_ui(self.layout, control=True)

    def refresh(self):
        """Refresh the details of the specified job, and update the UI."""
        self.base.update_job(self.index)
        maya.execute(self.base.get_thumbnail)
        self.selected_dir = utils.get_default_output_path()
        maya.text_field(self._dir, edit=True, text=self.selected_dir)
        maya.refresh()

    def start_watcher(self, *args):
        """Start the background job watcher. Command for watch_button."""
        utils.JobWatcher(
            self.base.selected_job_id(), self.data_path, self.selected_dir)

    def select_dir(self, *args):
        """Selected directory for job watcher to download outputs to.
        Command for directory select symbol button.
        """
        cap = "Select target directory for job downloads."
        okCap = "Select Folder"
        new_dir = maya.file_select(fileMode=3, okCaption=okCap, caption=cap)
        if new_dir:
            self.selected_dir = new_dir[0]
        maya.text_field(self._dir, edit=True, text=self.selected_dir)


    def display_info(self, label):
        """Display text data as a label with a heading.
        :param str label: The text for the data heading.
        """
        with utils.Row(2, 2, (100,220), ("right","left"),
                       parent=self.job_details) as row:
            self.content.append(row)
            self.content.append(maya.text(label=label, align="right"))
            input = maya.text(align="left", label="")
            self.content.append(input)
        return input, row

    def display_data(self, label):
        """Display text data as a non-editable text field with heading.
        :param str label: The text for the data heading.
        """
        with utils.Row(2, 2, (100,220), ("right","left"),
                       parent=self.job_details) as row:
            self.content.append(row)
            self.content.append(maya.text(label=label, align="right"))
            input = maya.text_field(text="", editable=False)
            self.content.append(input)
        return input, row

    def display_button(self, icon, cmd, note):
        """Display a job function button.

        :param str icon: The name of an icon to display on the button.
        :param func cmd: The command to execute when the button is clicked.
        :param str note: The tool tip text for the button.
        :returns: The button object.
        """
        img = os.path.join(os.environ["AZUREBATCH_ICONS"], icon)
        btn = maya.icon_button(style='iconOnly', image=img, flat=0,
                               height=30,
                               command=cmd,
                               parent=self.job_details,
                               enable=False, annotation=note)
        self.content.append(btn)
        return btn

    def display_watcher(self):
        """Display output download directory selection elements for
        job watcher.
        :returns: Text field object for directory path.
        """
        with utils.Row(3, 2, (100,190,40), ("right","center","center"),
                       parent=self.job_details) as row:
            self.content.append(row)
            self.content.append(maya.text(label="Outputs:   ", align="right"))
            input = maya.text_field(text=self.selected_dir, editable=False)
            self.content.append(maya.symbol_button(
                image="SP_DirOpenIcon.png",
                command=self.select_dir,
                annotation="Select Download Directory"))
        return input, row

    def set_thumbnail(self, thumb, height):
        """Set thumbnail image.

        :param str thumb: The path to the thumbnail image.
        :param int height: The height of the image in pixels.
        """
        maya.image(self._thumbnail,
                   edit=True,
                   image=thumb,
                   height=height)

    def cancel_job(self, *args):
        """Cancel the specified job. Command for cancel_button."""
        self.base.cancel_job()

    def delete_job(self, *args):
        """Cancel the specified job. Command for cancel_button."""
        self.base.delete_job()
