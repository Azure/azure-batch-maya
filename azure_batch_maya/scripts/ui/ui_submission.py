# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import azurebatchutils as utils

from azurebatchmayaapi import MayaAPI as maya
from ui_environment import PoolImageMode

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
        self.frame = frame
        self.label = "Submit"
        self.page = maya.form_layout(enableBackground=True)
        self.select_dedicated_instances = 1
        self.select_low_pri_instances = 0
        self.selected_container_image = None
        self.container_image_text_row = None
        self.container_image_dropdown_row = None
        self.persistent_pool_dropdown_row = None
        self.reused_pool_id = None
        self.container_config = []
        self.select_pool_type = self.AUTO_POOL
        with utils.ScrollLayout(height=475, parent=self.page) as scroll:
            box_label = "Pool Settings"
            with utils.FrameLayout(label=box_label, collapsable=True) as pool_settings:
                self.pool_settings = pool_settings
                with utils.ColumnLayout(
                        2, col_width=((1,100),(2,200)), row_spacing=(1,10),
                        row_offset=((1, "top", 20),(5, "bottom", 15))):
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
                    self.pool_config = []

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
                "Refresh", "Refreshing...", self.refresh_btn_clicked)

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
        self.set_pool_auto()
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

    def refresh_btn_clicked(self, *args):
        """Command for refresh_button.
        """
        self.refresh_button.start()
        self.base.env_manager.ui.refresh()
        self.refresh()
        self.refresh_button.finish()

    def refresh(self, *args):
        """Refresh Submit tab.
        Remove all existing UI elements and renderer details and re-build
        from scratch.
        """
        self.base.refresh_renderer(self.render_module)
        self.selected_dir = utils.get_default_output_path()
        maya.text_field(self.dir, edit=True, text=self.selected_dir)
        if self.persistent_pool_dropdown_row is not None:
            pool_options = self.base.available_pools()
            self.pool_dropdown.clear()
            self.pool_dropdown.add_item("")
            for pool_id in pool_options:
                self.pool_dropdown.add_item(pool_id)

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
            details = self.reused_pool_id
        else:
            details = (self.select_dedicated_instances, self.select_low_pri_instances)
        return {self.select_pool_type: details}

    def set_dedicated_instances(self, instances):
        """Update the number of requested instances in a pool
        based on the instance slider.
        """
        self.select_dedicated_instances = instances

    def set_low_pri_instances(self, instances):
        """Update the number of requested instances in a pool
        based on the instance slider.
        """
        self.select_low_pri_instances = instances

    def set_pool_new(self, *args):
        """Set selected pool type to be new pool of given size.
        Displays the pool size UI control.
        Command for select_pool_type radio buttons.
        """
        self.submit_enabled(True)
        self.select_pool_type = self.NEW_POOL
        maya.delete_ui(self.pool_config)
        if self.container_image_text_row is not None:
            maya.delete_ui(self.container_image_text_row)
        if self.container_image_dropdown_row is not None:
            maya.delete_ui(self.container_image_dropdown_row)
        if self.persistent_pool_dropdown_row is not None:
            maya.delete_ui(self.persistent_pool_dropdown_row)
            self.persistent_pool_dropdown_row = None
        self.pool_config = []
        with utils.ColumnLayout(4,
            col_width=((1, 100), (2, 50), (3, 100), (4, 50)),
            row_spacing=(1, 10),
            row_offset=(1, "bottom", 5),
            parent=self.pool_settings) as num_vms_column_layout:

            self.pool_config.append(num_vms_column_layout)
            self.pool_config.append(maya.text(
                label="Dedicated VMs:   ",
                align="right",
                parent=self.pool_config[0]))
            self.pool_config.append(maya.int_field(
                value=self.select_dedicated_instances,
                minValue=1,
                maxValue=self.base.max_pool_size,
                changeCommand=self.set_dedicated_instances,
                annotation="Number of dedicated VMs in pool",
                parent=self.pool_config[0]))
            self.pool_config.append(maya.text(
                label="Low-pri VMs:   ",
                align="right",
                parent=self.pool_config[0]))
            self.pool_config.append(maya.int_field(
                value=self.select_low_pri_instances,
                minValue=0,
                maxValue=self.base.max_pool_size,
                changeCommand=self.set_low_pri_instances,
                annotation="Number of low-priority VMs in pool",
                parent=self.pool_config[0]))

        available_images = self.base.env_manager.get_pool_container_images()
        if len(available_images) > 1:
            with utils.Row(1,1,100) as container_image_text_row:
                self.container_image_text_row = container_image_text_row
                self.pool_config.append(container_image_text_row)
                maya.text(label="Container Image to Render with:", align="left")

            with utils.Row(1, 1, 355, "left", (1, "bottom", 20), parent=self.pool_settings) as container_image_dropdown_row:
                self.container_image_dropdown_row = container_image_dropdown_row
                self.pool_config.append(container_image_dropdown_row)
                with utils.Dropdown(self.set_task_container_image, 
                    annotation="Select the Container Image to run the Render with",
                    width=355, parent=self.pool_config[-1]) as container_dropdown:
                    self.pool_config.append(container_dropdown)
                    for container_image in available_images:
                        container_dropdown.add_item(container_image)

    def set_pool_auto(self, *args):
        """Set selected pool type to be new pool of given size.
        Displays the pool size UI control.
        Command for select_pool_type radio buttons.
        """
        self.select_pool_type = self.AUTO_POOL
        self.submit_enabled(True)
        maya.delete_ui(self.pool_config)
        if self.container_image_text_row is not None:
            maya.delete_ui(self.container_image_text_row)
        if self.container_image_dropdown_row is not None:
            maya.delete_ui(self.container_image_dropdown_row)
        if self.persistent_pool_dropdown_row is not None:
            maya.delete_ui(self.persistent_pool_dropdown_row)
            self.persistent_pool_dropdown_row = None
        self.pool_config = []
        with utils.ColumnLayout(4,
            col_width=((1, 100), (2, 50), (3, 100), (4, 50)),
            row_spacing=(1, 10),
            row_offset=(1, "bottom", 5),
            parent=self.pool_settings) as num_vms_column_layout:
                self.pool_config.append(num_vms_column_layout)
                self.pool_config.append(maya.text(
                    label="Dedicated VMs:   ",
                    align="right",
                    parent=self.pool_config[0]))
                self.pool_config.append(maya.int_field(
                    value=self.select_dedicated_instances,
                    minValue=1,
                    maxValue=self.base.max_pool_size,
                    changeCommand=self.set_dedicated_instances,
                    annotation="Number of dedicated VMs in pool",
                    parent=self.pool_config[0]))
                self.pool_config.append(maya.text(
                    label="Low-pri VMs:   ",
                    align="right",
                    parent=self.pool_config[0]))
                self.pool_config.append(maya.int_field(
                    value=self.select_low_pri_instances,
                    minValue=0,
                    maxValue=self.base.max_pool_size,
                    changeCommand=self.set_low_pri_instances,
                    annotation="Number of low-priority VMs in pool",
                    parent=self.pool_config[0]))
        
        available_images = self.base.env_manager.get_pool_container_images()
        if len(available_images) > 1:
            with utils.Row(1,1,100) as container_image_text_row:
                self.container_image_text_row = container_image_text_row
                self.pool_config.append(container_image_text_row)
                maya.text(label="Container Image to Render with:", align="left")

            with utils.Row(1, 1, 355, "left", (1, "bottom", 10), parent=self.pool_settings) as container_image_dropdown_row:
                self.container_image_dropdown_row = container_image_dropdown_row
                self.pool_config.append(container_image_dropdown_row)
                with utils.Dropdown(self.set_task_container_image, 
                    annotation="Select the Container Image to run the Render with",
                    width=355, parent=self.pool_config[-1]) as container_dropdown:
                    self.pool_config.append(container_dropdown)
                    for container_image in available_images:
                        container_dropdown.add_item(container_image)

    def set_pool_reuse(self, *args):
        """Set selected pool type to be an existing pool with given ID.
        Loads the currently available pools and displays the pool IDs 
        in a dropdown menu.
        Command for select_pool_type radio buttons.
        """
        self.submit_enabled(False)
        self.select_pool_type = self.EXISTING_POOL
        maya.delete_ui(self.pool_config)
        if self.container_image_text_row is not None:
            maya.delete_ui(self.container_image_text_row)
        if self.container_image_dropdown_row is not None:
            maya.delete_ui(self.container_image_dropdown_row)
        if self.persistent_pool_dropdown_row is not None:
            maya.delete_ui(self.persistent_pool_dropdown_row)
        self.pool_config = []

        with utils.Row(1,1,100, parent=self.pool_settings) as reuse_pool_row:
            self.pool_config.append(reuse_pool_row)
            loading_message = maya.text(
                label="loading...",
                align="left")
            self.pool_config.append(loading_message)
            maya.refresh()
            pool_options = self.base.available_pools()
            maya.text(loading_message, edit=True, label="Reused Pool ID:   ")

        with utils.Row(1, 1, 355, "left", (1, "bottom", 5), parent=self.pool_settings) as persistent_pool_dropdown_row:
            self.persistent_pool_dropdown_row = persistent_pool_dropdown_row
            self.pool_config.append(persistent_pool_dropdown_row)

            with utils.Dropdown(self.reuse_selected_pool_dropdown_changed, annotation="Select an existing persistent pool.") as pool_dropdown:
                self.pool_config.append(pool_dropdown)
                self.pool_dropdown = pool_dropdown
                pool_dropdown.add_item("")
                for pool_id in pool_options:
                    pool_dropdown.add_item(pool_id)

    def reuse_selected_pool_dropdown_changed(self, poolId):
        maya.delete_ui(self.container_config)
        if self.container_image_text_row is not None:
            maya.delete_ui(self.container_image_text_row)
        if self.container_image_dropdown_row is not None:
            maya.delete_ui(self.container_image_dropdown_row)
        self.container_config = []
        self.reused_pool_id = poolId
        if not poolId:
            self.submit_enabled(False)
        else:
            self.submit_enabled(True)
            available_images = self.base.pool_manager.get_pool_container_images(poolId)
            if len(available_images) > 0:
                with utils.Row(1,1,100, parent=self.pool_settings) as container_image_text_row:
                    self.container_image_text_row = container_image_text_row
                    self.container_config.append(container_image_text_row)
                    maya.text(label="Container Image to Render with:   ", align="left")

                with utils.Row(1, 1, 355, "left", (1, "bottom", 10), parent=self.pool_settings) as container_image_dropdown_row:
                    self.container_image_dropdown_row = container_image_dropdown_row
                    self.container_config.append(container_image_dropdown_row)
                    with utils.Dropdown(self.set_task_container_image, 
                        annotation="Select the Container Image to run the Render with",
                        width=355) as container_dropdown:
                        #self.container_config.append(container_dropdown)
                        for container_image in available_images:
                            container_dropdown.add_item(container_image)
    
    def set_task_container_image(self, selected_container_image):
        self.selected_container_image = selected_container_image

    def get_task_container_image(self):
        if self.select_pool_type == self.EXISTING_POOL:
            return self.selected_container_image
        if self.select_pool_type == self.AUTO_POOL or self.select_pool_type == self.NEW_POOL:
            return self.base.env_manager.get_task_container_image()
