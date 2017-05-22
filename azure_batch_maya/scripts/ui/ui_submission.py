# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import utils

from api import MayaAPI as maya


class SubmissionUI(object):
    """Class to create the 'Submit' tab in the plug-in UI"""

    AUTO_POOL = 1
    EXISTING_POOL = 2
    NEW_POOL = 3


    def __init__(self, base, frame):
        """Create 'Submit' tab and add to UI frame.

        :param base: The base class for handling jobs submission functionality.
        :type base: :class:`.AzureBatchSubmission`
        :param frame: The shared plug-in UI frame.
        :type frame: :class:`.AzureBatchUI`
        """
        self.base = base
        self.label = "Submit"
        self.page = maya.form_layout(enableBackground=True) 
        self.select_pool_type = self.AUTO_POOL
        self.select_instances = 1
        
        with utils.ScrollLayout(height=475, parent=self.page) as scroll:
            box_label = "Pool Settings"
            with utils.FrameLayout(label=box_label, collapsable=True):
                self.pool_settings = maya.col_layout(
                    numberOfColumns=2,
                    columnWidth=((1, 100), (2, 200)),
                    rowSpacing=(1, 10),
                    rowOffset=((1, "top", 20), (2, "bottom", 20)))
                maya.text(label="Pools:   ", align="right")
                maya.radio_group(
                    labelArray3=("Auto provision a pool for this job",
                                 "Reuse an existing persistent pool",
                                 "Create a new persistent pool"),
                    numberOfRadioButtons=3,
                    select=self.select_pool_type,
                    vertical=True,
                    onCommand1=self.set_pool_auto,
                    onCommand2=self.set_pool_reuse,
                    onCommand3=self.set_pool_new)
                self.pool_text = maya.text(
                    label="Instances:   ", align="right")
                self.control = maya.int_slider(
                    field=True, value=self.select_instances,
                    minValue=1,
                    maxValue=self.base.max_pool_size,
                    fieldMinValue=1,
                    fieldMaxValue=self.base.max_pool_size,
                    changeCommand=self.set_pool_instances,
                    annotation="Number of instances in pool")
                maya.parent()

            box_label = "Render Settings"
            with utils.FrameLayout(label=box_label, collapsable=True) as box:
                self.render_module = box

        with utils.Row(3, 2, (120,200,35)) as watch:
            self.job_watcher_ui()

        with utils.Row(1, 1, 355, "center") as s_btn:
            self.submit_button = utils.ProcButton(
                "Submit Job", "Submitting...", self.submit)

        with utils.Row(1, 1, 355, "center", (1,"bottom",0)) as r_btn:
            self.refresh_button = utils.ProcButton(
                "Refresh", "Refreshing...", self.refresh)

        maya.form_layout(
            self.page, edit=True,
            attachForm=[(scroll, 'top', 5),
                        (scroll, 'left', 5), (scroll, 'right', 5),
                        (watch, 'left', 0), (watch, 'right', 0),
                        (s_btn, 'left', 0), (s_btn, 'right', 0),
                        (r_btn, 'bottom', 5),
                        (r_btn, 'left', 0), (r_btn, 'right', 0)],
            attachControl=[(scroll, "bottom", 5, watch),
                           (watch, "bottom" ,5, s_btn),
                           (s_btn, "bottom", 5, r_btn)])
        frame.add_tab(self)

    def job_watcher_ui(self):
        """Create UI elements for enabling and configuring job watcher."""
        self.watch_job = maya.check_box(
            label="Watch this job",
            onCommand=lambda e: self.enable_watcher(True),
            offCommand=lambda e: self.enable_watcher(False),
            annotation="Watching a job will download tasks as they complete.")
        self.selected_dir = utils.get_default_output_path()
        self.dir = maya.text_field(text=self.selected_dir, editable=False)
        self.dir_button = maya.symbol_button(
            image="SP_DirOpenIcon.png",
            command=self.select_dir,
            annotation="Select Download Directory")

    def select_dir(self, *args):
        """Selected directory for job watcher to download outputs to.
        Command for directory select symbol button.
        """
        cap = "Select target directory for job downloads."
        okCap = "Select Folder"
        new_dir = maya.file_select(fileMode=3, okCaption=okCap, caption=cap)
        if new_dir:
            self.selected_dir = new_dir[0]
        maya.text_field(self.dir, edit=True, text=self.selected_dir)

    def enable_watcher(self, opt):
        """Enable whether job watcher will be launched after submission.
        Command for watch_job check box.
        :param bool opt: True if watcher enabled.
        """
        maya.symbol_button(self.dir_button, edit=True, enable=opt)
        maya.text_field(
            self.dir, edit=True, enable=opt, text=self.selected_dir)

    def is_logged_in(self):
        """Called when the plug-in is authenticated. Enables UI."""
        maya.form_layout(self.page, edit=True, enable=True)

    def is_logged_out(self):
        """Called when the plug-in is logged out. Disables UI and resets
        whether that tab has been loaded for the first time.
        """
        maya.form_layout(self.page, edit=True, enable=False)

    def prepare(self):
        """Prepare Submit tab contents - nothing needs to be done here as all
        loaded on plug-in start up.
        """
        pass

    def refresh(self, *args):
        """Refresh Submit tab. Command for refresh_button.
        Remove all existing UI elements and renderer details and re-build
        from scratch.
        """
        self.refresh_button.start()
        self.base.refresh_renderer(self.render_module)
        self.selected_dir = utils.get_default_output_path()
        maya.text_field(self.dir, edit=True, text=self.selected_dir)
        self.refresh_button.finish()

    def submit_status(self, status):
        """Report submission status in UI. Called from base class.
        Displays status in the submit_button label.
        :param str status: The status string to display.
        """
        self.submit_button.update(status)

    def submit(self, *args):
        """Submit new job. Command for submit_button."""
        self.submit_button.start()
        self.refresh_button.enable(False)
        self.enable_watcher(False)
        maya.check_box(self.watch_job, edit=True, enable=False)
        watcher = maya.check_box(self.watch_job, query=True, value=True)
        if watcher and not self.selected_dir:
            maya.warning("You must select a download directory "
                         "if you wish to watch this job.")
        else:
            self.base.submit(watcher, self.selected_dir)
        maya.check_box(self.watch_job, edit=True, enable=True)
        self.enable_watcher(True)
        self.submit_button.finish()
        self.refresh_button.enable(True)

    def submit_enabled(self, enable):
        """Enable or disable users ability to submit a job based on renderer
        conditions.
        :param bool enable: Whether to enable to submission.
        """
        maya.check_box(self.watch_job, edit=True, enable=enable)
        maya.button(self.dir_button, edit=True, enable=False)
        maya.button(self.submit_button.display, edit=True, enable=enable)

    def get_pool(self):
        """Get selected pool configuration.
        :returns: A dictionary with selected pool type as key and pool
         specification as value.
        """
        if self.select_pool_type == self.EXISTING_POOL:
            details = str(maya.menu(self.control, query=True, value=True))
        else:
            details = self.select_instances
        return {self.select_pool_type: details}

    def set_pool_instances(self, instances):
        """Update the number of requested instances in a pool
        based on the instance slider.
        """
        self.select_instances = instances

    def set_pool_new(self, *args):
        """Set selected pool type to be new pool of given size.
        Displays the pool size UI control.
        Command for select_pool_type radio buttons.
        """
        self.select_pool_type = self.NEW_POOL
        maya.delete_ui(self.control)
        maya.text(self.pool_text, edit=True, label="Instances:   ")
        self.control = maya.int_slider(
            field=True,
            value=self.select_instances,
            minValue=1,
            maxValue=self.base.max_pool_size,
            fieldMinValue=1,
            fieldMaxValue=self.base.max_pool_size,
            parent=self.pool_settings,
            changeCommand=self.set_pool_instances,
            annotation="Number of instances in pool")

    def set_pool_auto(self, *args):
        """Set selected pool type to be new pool of given size.
        Displays the pool size UI control.
        Command for select_pool_type radio buttons.
        """
        self.select_pool_type = self.AUTO_POOL
        maya.delete_ui(self.control)
        maya.text(self.pool_text, edit=True, label="Instances:   ")
        self.control = maya.int_slider(
            field=True,
            value=self.select_instances,
            minValue=1,
            maxValue=self.base.max_pool_size,
            fieldMinValue=1,
            fieldMaxValue=self.base.max_pool_size,
            parent=self.pool_settings,
            changeCommand=self.set_pool_instances,
            annotation="Number of instances in pool")

    def set_pool_reuse(self, *args):
        """Set selected pool type to be an existing pool with given ID.
        Loads the currently available pools and displays the pool IDs 
        in a dropdown menu.
        Command for select_pool_type radio buttons.
        """
        self.select_pool_type = self.EXISTING_POOL
        maya.delete_ui(self.control)
        maya.text(self.pool_text, edit=True, label="loading...")
        maya.refresh()
        pool_options = self.base.available_pools()
        maya.text(self.pool_text, edit=True, label="Pool ID:   ")
        self.control = maya.menu(
            parent=self.pool_settings,
            annotation="Use an existing persistent pool ID")
        for pool_id in pool_options:
            maya.menu_option(pool_id)
