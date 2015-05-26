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

    def __init__(self, **kwargs):
        self.form = maya.row_layout

        self.layout = self.form()
        if kwargs.get("width"):
            self.width = kwargs.get("width")

        if kwargs.get("height"):
            self.height = kwargs["height"]

        if kwargs.get("parent"):
            self.parent = kwargs.get("parent")

        if kwargs.get("row_spacing"):
            self.row_space = kwargs.get("row_spacing")

        if kwargs.get("col_attach"):
            self.column_attach = kwargs.get("col_attach")


    def __enter__(self):
        return self.layout

    def __exit__(self, type, value, traceback):
        #TODO: Exception handling should go in here
        maya.parent()

    @property
    def parent(self):
        return self.form(self.layout, query=True, parent=True)

    @parent.setter
    def parent(self, value):
        self.form(self.layout, edit=True, parent=value)

    @property
    def width(self):
        return self.form(self.layout, query=True, width=True)

    @width.setter
    def width(self, value):
        self.form(self.layout, edit=True, width=value)

    @property
    def height(self):
        return self.form(self.layout, query=True, width=True)

    @height.setter
    def height(self, value):
        self.form(self.layout, edit=True, height=value)

    @property
    def row_space(self):
        return self.form(self.layout, query=True, rowSpacing=True)

    @width.setter
    def row_space(self, value):
        self.form(self.layout, edit=True, rowSpacing=value)

    @property
    def column_attach(self):
        return self.form(self.layout, query=True, columnAttach=True)

    @width.setter
    def column_attach(self, value):
        self.form(self.layout, edit=True, columnAttach=value)

class FrameLayout(Layout):

    def __init__(self, **kwargs):
        self.form = maya.frame_layout

        super(FrameLayout, self).__init__(**kwargs)

        if kwargs.get("label"):
            self.label = kwargs.get("label")

        if kwargs.get("collapsable"):
            self.collapsable = kwargs.get("collapsable")

    @property
    def label(self):
        return self.form(self.layout, query=True, label=True)

    @label.setter
    def label(self, value):
        self.form(self.layout, edit=True, label=value)

    @property
    def collapsable(self):
        return self.form(self.layout, query=True, collapsable=True)

    @collapsable.setter
    def collapsable(self, value):
        self.form(self.layout, edit=True, collapsable=value)

class ColumnLayout(Layout):

    def __init__(self, columns, **kwargs):
        self.form = maya.col_layout

        self.layout = self.form(numberOfColumns=columns)

        if kwargs.get("col_width"):
            self.col_width = kwargs["col_width"]

        if kwargs.get("row_offset"):
            self.row_offset = kwargs["row_offset"]

        if kwargs.get("row_spacing"):
            self.row_space = kwargs.get("row_spacing")

        if kwargs.get("row_height"):
            self.row_height = kwargs["row_height"]

    @property
    def col_width(self):
        return self.form(self.layout, query=True, columnWidth=True)

    @col_width.setter
    def col_width(self, value):
        self.form(self.layout, edit=True, columnWidth=value)

    @property
    def row_offset(self):
        return self.form(self.layout, query=True, rowOffset=True)

    @row_offset.setter
    def row_offset(self, value):
        self.form(self.layout, edit=True, rowOffset=value)

    @property
    def row_height(self):
        return self.form(self.layout, query=True, rowHeight=True)

    @row_height.setter
    def row_height(self, value):
        self.form(self.layout, edit=True, rowHeight=value)

class ScrollLayout(Layout):

    def __init__(self, **kwargs):
        self.form = maya.scroll_layout

        self.layout = self.form(horizontalScrollBarThickness=0)
        
        if kwargs.get("width"):
            self.width = kwargs["width"]

        if kwargs.get("height"):
            self.height = kwargs["height"]

        if kwargs.get("v_scrollbar"):
            self.vertical_scrollbar = kwargs["v_scrollbar"]

    @property
    def vertical_scrollbar(self):
        return self.form(self.layout, query=True, verticalScrollBarThickness=True)

    @vertical_scrollbar.setter
    def vertical_scrollbar(self, value):
        self.form(self.layout, edit=True, verticalScrollBarThickness=value)
