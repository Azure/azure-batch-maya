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

from api import MayaAPI as maya

class Layout(object):

    def __init__(self, form, **kwargs):

        self.form = form

        settings = {}
        
        if kwargs.get("width"):
            settings["width"] = kwargs["width"]

        if kwargs.get("height"):
            settings["height"] = kwargs["height"]

        if kwargs.get("parent"):
            settings["parent"] = kwargs["parent"]

        if kwargs.get("row_spacing"):
            settings["rowSpacing"] = kwargs["row_spacing"]

        if kwargs.get("col_attach"):
            settings["columnAttach"] = kwargs["col_attach"]

        if kwargs.get("layout"):
            settings.update(kwargs["layout"])

        self.layout = self.form(**settings)


    def __enter__(self):
        return self.layout

    def __exit__(self, type, value, traceback):
        #TODO: Exception handling should go in here
        maya.parent()


class RowLayout(Layout):

    def __init__(self, **kwargs):
        super(RowLayout, self).__init__(maya.row_layout, **kwargs)


class FrameLayout(Layout):

    def __init__(self, **kwargs):

        settings = {}

        if kwargs.get("label"):
            settings["label"] = kwargs["label"]

        if kwargs.get("collapsable"):
            settings["collapsable"] = kwargs["collapsable"]

        super(FrameLayout, self).__init__(maya.frame_layout, layout=settings, **kwargs)


class ColumnLayout(Layout):

    def __init__(self, columns, **kwargs):

        settings = {"numberOfColumns": columns}

        if kwargs.get("col_width"):
            settings["columnWidth"] = kwargs["col_width"]

        if kwargs.get("row_offset"):
            settings["rowOffset"] = kwargs["row_offset"]

        if kwargs.get("row_height"):
            settings["rowHeight"] = kwargs["row_height"]

        super(ColumnLayout, self).__init__(maya.col_layout, layout=settings, **kwargs)


class ScrollLayout(Layout):

    def __init__(self, **kwargs):

        settings = {"horizontalScrollBarThickness": 0,
                    "verticalScrollBarThickness": 3}

        super(ScrollLayout, self).__init__(maya.scroll_layout, layout=settings, **kwargs)


class Dropdown(object):

    def __init__(self, command, **kwargs):

        self.menu = maya.menu(changeCommand=command, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        maya.parent()

    def add_item(self, item):
        maya.menu_option(label=item, parent=self.menu)

    def selected(self):
        return int(maya.menu(self.menu, query=True, select=True))

    def value(self):
        return str(maya.menu(self.menu, query=True, value=True))

    def select(self, value):
        maya.menu(self.menu, edit=True, select=int(value))