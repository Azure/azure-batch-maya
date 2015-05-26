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

class PoolsUI(object):

    def __init__(self, base, frame):

        self.base = base
        self.label = " Pools  "
        self.ready = False

        self.pools_displayed = []

        with utils.Layout(width=360) as layout:
            self.page = layout

            with utils.ScrollLayout(v_scrollbar=3, h_scrollbar=0, width=355, height=520) as scroll:
        
                with utils.Layout(row_spacing=20) as sublayout:

                    if not self.pools_displayed:
                        self.empty_pools = maya.text(
                            label="Loading pool data...",
                            font="boldLabelFont",
                            parent=sublayout)

                    self.pools_layout = sublayout

            with utils.ColumnLayout(1, col_width=(1,355)) as col:
                maya.button(label="Refresh", command=self.refresh)

        frame.add_tab(self)
        self.is_logged_out()

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
                maya.error("Error starting Pools UI: {0}".format(exp))
                self.is_logged_out()

        maya.refresh()

    def refresh(self, *k):
        try:
            maya.delete_ui(self.empty_pools)
        except RuntimeError:
            pass

        self.base.pool_selected(None)
        for i in self.pools_displayed:
            i.remove()

        self.pools_displayed = self.base.get_pools()
        if not self.pools_displayed:
            self.empty_pools = maya.text(label="No pools to display",
                                         parent=self.pools_layout)
                

    def create_pool_entry(self, name, index):
        frame = maya.frame_layout(label=name,
                                    collapsable=True,
                                    collapse=True,
                                    borderStyle='in',
                                    width=345,
                                    visible=True,
                                    parent=self.pools_layout)

        return BatchAppsPoolInfo(self.base, index, frame)


class BatchAppsPoolInfo:

    def __init__(self, base, index, layout):
        
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
            columnWidth=((1, 100),
                         (2, 200)),
            rowSpacing=((1, 5),),
            rowOffset=((1, "top", 5),(1, "bottom", 5),),
            parent=self.layout)

        self.content = []


    def set_label(self, value):
        maya.frame_layout(self.layout, edit=True, label=value)

    def set_type(self, value):
        maya.text(self._type, edit=True, label=" {0}".format(value))

    def set_size(self, value):
        maya.text(self._size, edit=True, label=" {0}".format(value))

    def set_target(self, value):
        maya.text(self._target, edit=True, label=" {0}".format(value))

    def set_created(self, value):
        datetime = value.split('T')
        datetime[1] = datetime[1].split('.')[0]
        label = ' '.join(datetime)
        maya.text(self._created, edit=True, label=" {0}".format(label))

    def set_state(self, value):
        maya.text(self._state, edit=True, label=" {0}".format(value))

    def set_tasks(self, value):
        maya.text(self._tasks, edit=True, label=" {0}".format(value))

    def set_allocation(self, value):
        maya.text(self._allocation, edit=True, label=" {0}".format(value))

    def change_resize_label(self, label, enable=True):
        maya.button(self.resize_button, edit=True, label="{0}".format(label), enable=enable)

    def on_expand(self):

        self._type = self.display_info("Type:   ")
        self._size = self.display_info("Current Size:   ")
        self._target = self.display_info("Target Size:   ")
        self._created = self.display_info("Created:   ")
        self._state = self.display_info("State:   ")
        self._tasks = self.display_info("Tasks per VM:   ")
        self._allocation = self.display_info("Allocation State:   ")
        
        self.base.pool_selected(self)

        auto = self.base.is_auto_pool()
        if not auto:

            self.resize_button = self.button("Resize Pool", self.resize_pool, self.listbox)
            self.resize_int = maya.int_slider(
                value=self.base.get_pool_size(),
                minValue=1,
                maxValue=1000,
                fieldMinValue=1,
                fieldMaxValue=100,
                field=True,
                width=200,
                parent=self.listbox,
                annotation="Number of instances to work in pool.")
            self.content.extend([self.resize_button, self.resize_int])

        self.content.append(self.button("Delete Pool", self.delete_pool, self.layout))

        maya.refresh()

    def on_collapse(self):
        self.base.pool_selected(None)
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

    def display_info(self, label):
        self.content.append(maya.text(label=label, parent=self.listbox, align="right"))
        input = maya.text(align="left", label="", parent=self.listbox)
        self.content.append(input)
        return input

    def button(self, label, command, p):
        return maya.button(label=label,
                           parent=p,
                           align="center",
                           command=command)

    def delete_pool(self, *args):
        self.base.delete_pool()
        #self.base.refresh()

    def resize_pool(self, *args):
        self.change_resize_label("Resizing...", enable=False)
        maya.refresh()

        resize = maya.int_slider(self.resize_int, query=True, value=True)
        self.base.resize_pool(resize)
        self.base.update_pool(self.index)

        self.change_resize_label("Resize Pool")