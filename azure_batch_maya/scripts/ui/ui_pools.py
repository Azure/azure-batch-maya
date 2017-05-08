#-------------------------------------------------------------------------
#
# Azure Batch Maya Plugin
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
            columnWidth=((1, 100), (2, 200)),
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

    def set_size(self, value):
        """Set the number of instances in the pool.
        :param int value: Size of the pool.
        """
        maya.text(self._size, edit=True, label=" {0}".format(value))

    def set_target(self, value):
        """Set the target number of instances in the pool.
        :param int value: The target size of the pool.
        """
        maya.text(self._target, edit=True, label=" {0}".format(value))

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

    def set_tasks(self, value):
        """Set the tasks per TVM allowed in the pool.
        :param int value: Tasks per TVM.
        """
        maya.text(self._tasks, edit=True, label=" {0}".format(value))

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

    def on_expand(self):
        """Command for the expanding of the pool reference frame layout.
        Loads latest details for the specified pool and populates UI.
        """
        self._type = self.display_info("Type:   ")
        self._size = self.display_info("Current Size:   ")
        self._target = self.display_info("Target Size:   ")
        self._created = self.display_info("Created:   ")
        self._state = self.display_info("State:   ")
        self._tasks = self.display_info("Tasks per VM:   ")
        self._allocation = self.display_info("Allocation State:   ")
        self._licenses = self.display_info("Licenses:   ")
        self._vm_sku = self.display_info("VM type:   ")
        self.base.pool_selected(self)
        auto = self.base.is_auto_pool()
        if not auto:
            self.resize_button = utils.ProcButton(
                "Resize Pool", "Resizing...", self.resize_pool,
                parent=self.listbox, align="center")
            self.resize_int = maya.int_slider(
                value=self.base.get_pool_size(),
                minValue=0,
                maxValue=1000,
                fieldMinValue=0,
                fieldMaxValue=100,
                field=True,
                width=230,
                parent=self.listbox,
                annotation="Number of instances to work in pool.")
            self.content.append(self.resize_button.display)
            self.content.append(self.resize_int)
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

    def delete_pool(self, *args):
        """Delete the specified pool."""
        self.delete_button.start()
        self.base.delete_pool()   
        self.delete_button.finish() 

    def resize_pool(self, *args):
        """Resize the specified pool."""
        self.resize_button.start()
        resize = maya.int_slider(self.resize_int, query=True, value=True)
        self.base.resize_pool(resize)
        self.base.update_pool(self.index)
        self.resize_button.finish()
