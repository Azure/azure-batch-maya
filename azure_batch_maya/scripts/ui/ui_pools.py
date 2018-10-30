# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azurebatchmayaapi import MayaAPI as maya

import azurebatchutils as utils

class PoolsUI(object):
    """Class to create the 'Pools' tab in the plug-in UI"""

    def __init__(self, base, frame):
        """Create 'Pools' tab and add to UI frame.

        :param base: The base class for handling pools monitoring functionality.
        :type base: :class:`.AzureBatchPools`
        :param frame: The shared plug-in UI frame.
        :type frame: :class:`.AzureBatchUI`
        """
        self.base = base
        self.label = "Pools "
        self.ready = False
        self.pools_displayed = []
        self.page = maya.form_layout(enableBackground=True)
        with utils.ScrollLayout(
            v_scrollbar=3, h_scrollbar=0, height=520) as scroll:
            with utils.RowLayout(row_spacing=20) as sublayout:
                if not self.pools_displayed:
                    self.empty_pools = maya.text(
                        label="Loading pool data...",
                        font="boldLabelFont",
                        parent=sublayout)
                self.pools_layout = sublayout
        with utils.Row(1, 1, 355, "center", (1,"bottom",0)) as btn:
            self.refresh_button = utils.ProcButton(
                "Refresh", "Refreshing...", self.refresh)
        maya.form_layout(self.page, edit=True,
                         attachForm=[(scroll, 'top', 5),
                                     (scroll, 'left', 5), (scroll, 'right', 5),
                                     (btn, 'bottom', 5),
                                     (btn, 'left', 0), (btn, 'right', 0)],
                         attachControl=(scroll, "bottom", 5, btn))
        frame.add_tab(self)
        self.is_logged_out()

    def is_logged_in(self):
        """Called when the plug-in is authenticated. Enables UI."""
        maya.form_layout(self.page, edit=True, enable=True)

    def is_logged_out(self):
        """Called when the plug-in is logged out. Disables UI and resets
        whether that tab has been loaded for the first time.
        """
        maya.delete_ui(self.empty_pools)
        self.base.pool_selected(None)
        for i in self.pools_displayed:
            i.remove()

        self.pools_displayed = []
        self.empty_pools = maya.text(label="No pools to display",parent=self.pools_layout)

        maya.form_layout(self.page, edit=True, enable=False)
        self.ready = False

    def prepare(self):
        """Called when the tab is loaded (clicked into) for the first time.
        Initiates the downloading of pools details.
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
                maya.error("Error starting Pools UI: {0}".format(exp))
                self.is_logged_out()
        maya.refresh()

    def refresh(self, *args):
        """Refresh Pools tab. Command for refresh_button.
        Remove all existing UI elements and pool details and re-build
        from scratch. This is also called to populate 
        the tab for the first time.
        """
        self.refresh_button.start()
        maya.delete_ui(self.empty_pools)
        self.base.pool_selected(None)
        for i in self.pools_displayed:
            i.remove()
        self.pools_displayed = self.base.get_pools()
        if not self.pools_displayed:
            self.empty_pools = maya.text(label="No pools to display",
                                         parent=self.pools_layout)
        self.refresh_button.finish()

    def create_pool_entry(self, name, index):
        """Create new dropdown frame to represent a pool entry.
        :returns: A :class:`.AzureBatchPoolInfo` object.
        """
        frame = maya.frame_layout(label=name,
                                    collapsable=True,
                                    collapse=True,
                                    width=345,
                                    visible=True,
                                    parent=self.pools_layout)
        return AzureBatchPoolInfo(self.base, index, frame)


class AzureBatchPoolInfo(object):
    """Class to represent a single pool reference."""

    def __init__(self, base, index, layout):
        """Create a new pool reference.

        :param base: The base class for handling pools monitoring functionality.
        :type base: :class:`.AzureBatchPools`
        :param int index: The index of where this reference is displayed on
         the current page.
        :param layout: The layout on which the pool details will be displayed.
        :type layout: :class:`.utils.FrameLayout`
        """
        self.base = base
        self.index = index
        self.layout = layout
        maya.frame_layout(
            layout,
            edit=True,
            collapseCommand=self.on_collapse,
            expandCommand=self.on_expand)
        self.listbox = maya.col_layout(
            numberOfColumns=2,
            columnWidth=((1, 120), (2, 200)),
            rowSpacing=((1, 5),),
            rowOffset=((1, "top", 5),(1, "bottom", 5),),
            parent=self.layout)
        self.content = []

    def set_label(self, value):
        """Set the label for the pool frame layout.
        :param str value: The string to display as label.
        """
        maya.frame_layout(self.layout, edit=True, label=value)

    def set_type(self, value):
        """Set the type of the pool - auto or provisioned.
        :param str value: The pool type.
        """
        maya.text(self._type, edit=True, label=" {0}".format(value))

    def set_image_type(self, value):
        """Set the type of the pool - vm image or container.
        :param str value: The pool image type.
        """
        maya.text(self._type, edit=True, label=" {0}".format(value))

    def set_dedicated_size(self, pool):
        """Set the number of instances in the pool, both current and target.
        :param int value: Size of the pool.
        """
        maya.text(self._dedicated_size, edit=True, label=" target: {} current: {}".format(
            pool.target_dedicated_nodes, pool.current_dedicated_nodes))

    def set_low_pri_size(self, pool):
        """Set the number of instances in the pool, both current and target.
        :param int value: Size of the pool.
        """
        maya.text(self._low_pri_size, edit=True, label=" target: {} current: {}".format(
            pool.target_low_priority_nodes, pool.current_low_priority_nodes))

    def set_created(self, value):
        """Set the date/time the pool was created.
        :param str value: The datetime string of the pool creation.
        """
        datetime = str(value).split('.')[0]
        maya.text(self._created, edit=True, label=" {0}".format(datetime))

    def set_state(self, value, nodes):
        """Set the state of the pool.
        :param str value: The pool state.
        """
        node_states = {}
        for node in nodes:
            if node.state in node_states:
                node_states[node.state] += 1
            else:
                node_states[node.state] = 1
        if node_states:
            value += " : "
            for state in node_states:
                value += "{} nodes {} ".format(node_states[state], state.value)
        maya.text(self._state, edit=True, label=" {0}".format(value))

    def set_id(self, value):
        """Set the pool ID field.
        :param str value: Pool ID.
        """
        maya.text_field(self._id, edit=True, text=value)

    def set_allocation(self, value):
        """Set the allocation state of the pool.
        :param str value: The pool allocation state.
        """
        maya.text(self._allocation, edit=True, label=" {0}".format(value))

    def set_licenses(self, value):
        """Set the licenses available on the pool.
        :param list value: The available application licenses.
        """
        licenses = ', '.join([l.title() for l in value]) if value else ""
        maya.text(self._licenses, edit=True, label=" {0}".format(licenses))

    def set_vm_sku(self, value):
        """Set the VM instance type of the pool.
        :param str value: The VM type.
        """
        maya.text(self._vm_sku, edit=True, label=" {0}".format(value))

    def set_image(self, value):
        """Set the image name running on the VM.
        :param str value: The VM image.
        """
        maya.text(self._image, edit=True, label=" {0}".format(value))

    def set_container_images_table(self, container_images):
        """Set the container image table up for the pool.
        Sets the class field for the image to add and calls insertRow, which triggers 
        :param str value: The VM image.
        """
        self._container_images = container_images
        if container_images:
            table_height = max(60, min(150, 25 + 15 * len(container_images)))
            maya.table(self._container_images_table, edit=True, clearTable=True, visible=True, height= table_height)
        for image in container_images:
            self.container_image_to_add = image
            maya.table(self._container_images_table, edit=True, insertRow=1)

    def on_expand(self):
        """Command for the expanding of the pool reference frame layout.
        Loads latest details for the specified pool and populates UI.
        """
        self._id = self.display_data("ID:   ")
        self._type = self.display_info("Type:   ")
        self._dedicated_size = self.display_info("Dedicated VMs:   ")
        self._low_pri_size = self.display_info("Low Priority VMs:   ")
        self._created = self.display_info("Created:   ")
        self._state = self.display_info("State:   ")
        self._image = self.display_info("Image:   ")
        self._allocation = self.display_info("Allocation State:   ")
        self._allocation = self.display_info("Allocation State:   ")
        self._licenses = self.display_info("Licenses:   ")
        self._vm_sku = self.display_info("VM type:   ")
        
        self._container_images = None
        self._container_images_table = self.display_table("Container Images:   ", lambda row, column: self.container_image_to_add)
        maya.table(self._container_images_table, edit=True, visible=False)
        self.base.pool_selected(self)

        auto = self.base.is_auto_pool()
        if not auto:
            self.content.append(maya.col_layout(
                numberOfColumns=5,
                columnWidth=((1, 80), (2, 100), (3, 45), (4, 80), (5, 45)),
                rowSpacing=(1, 10),
                parent=self.layout))
            self.resize_button = utils.ProcButton(
                "Resize Pool",
                "Resizing...",
                self.resize_pool,
                parent=self.content[-1],
                align="center")
            self.dedicated_label = maya.text(
                label="Dedicated VMs",
                parent=self.content[-1])
            self.resize_dedicated = maya.int_field(
                value=self.base.get_pool_size()[0],
                minValue=0,
                maxValue=1000,
                parent=self.content[-1],
                annotation="Number of dedicated VMs in pool.")
            self.low_pri_label = maya.text(
                label="Low-pri VMs",
                parent=self.content[-1])
            self.resize_low_pri = maya.int_field(
                value=self.base.get_pool_size()[1],
                minValue=0,
                maxValue=1000,
                parent=self.content[-1],
                annotation="Number of Low-priority VMs in pool.")
            self.content.append(self.resize_button.display)
            self.content.append(self.dedicated_label)
            self.content.append(self.resize_dedicated)
            self.content.append(self.low_pri_label)
            self.content.append(self.resize_low_pri)
        self.delete_button = utils.ProcButton("Delete Pool", "Deleting...",
            self.delete_pool, parent=self.layout, align="center")
        self.content.append(self.delete_button.display)
        maya.refresh()

    def on_collapse(self):
        """Command for the collapsing of the pool reference frame layout.
        Deletes all UI elements and resets currently selected pool.
        This is called automatically when the user collapses the UI layout,
        or programmatically from the :func:`collapse` function.
        """
        self.base.pool_selected(None)
        maya.parent(self.listbox)
        for element in self.content:
            maya.delete_ui(element, control=True)
        self.content = []

    def collapse(self):
        """Collapse the pool frame. Initiates the on_collapse sequence."""
        maya.frame_layout(self.layout, edit=True, collapse=True)
        self.on_collapse()
        maya.refresh()

    def remove(self):
        """Delete the pool reference frame layout."""
        maya.delete_ui(self.layout, control=True)

    def display_info(self, label):
        """Display text data as a label with a heading.
        :param str label: The text for the data heading.
        """
        self.content.append(
            maya.text(label=label, parent=self.listbox, align="right"))
        input = maya.text(align="left", label="", parent=self.listbox)
        self.content.append(input)
        return input

    def display_data(self, label):
        """Display text data as a non-editable text field with heading.
        :param str label: The text for the data heading.
        """
        self.content.append(
            maya.text(label=label, parent=self.listbox, align="right"))
        input = maya.text_field(text="", parent=self.listbox, editable=False)
        self.content.append(input)
        return input

    def display_table(self, label, populate_contents_func):
        layout_width = 355
        layout = maya.col_layout(
            columnWidth=(1, layout_width),
            adjustableColumn=True,
            columnAttach=(1, 'both', 10),
            numberOfColumns=1,
            parent=self.layout)

        table = maya.table(height=60,
            rows=0, columns=2, columnWidth=[(1, layout_width - 6), (2, 1)], rowHeight=15,
            label=[(1, label), (2, "")],
            selectionBehavior=0,
            editable=False,
            getCellCmd=populate_contents_func,
            parent=layout)

        self.content.append(layout)
        self.content.append(table)
        return table

    def delete_pool(self, *args):
        """Delete the specified pool."""
        self.delete_button.start()
        self.base.delete_pool()   
        self.delete_button.finish() 

    def resize_pool(self, *args):
        """Resize the specified pool."""
        self.resize_button.start()
        resize_dedicated = maya.int_field(self.resize_dedicated, query=True, value=True)
        resize_low_pri = maya.int_field(self.resize_low_pri, query=True, value=True)
        self.base.resize_pool(resize_dedicated, resize_low_pri)
        self.base.update_pool(self.index)
        self.resize_button.finish()
