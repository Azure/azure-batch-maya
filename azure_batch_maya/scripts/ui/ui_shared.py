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


class AzureBatchUI(object):
    """Class to create the plug-in UI frame into which all the tabs 
    will be loaded.
    """

    def __init__(self, base):
        """Create and open plug-in UI."""
        self.base = base
        if (maya.window("AzureBatch", q=1, exists=1)):
            maya.delete_ui("AzureBatch")
        self.ui = maya.window("AzureBatch",
                              title="Azure Batch Maya Client v{0}".format(
                                  os.environ["AZUREBATCH_VERSION"]),
                              sizeable=True,
                              height=450,
                              resizeToFitChildren=True)
        self.form = maya.form_layout()
        self.tab_display = maya.tab_layout(innerMarginWidth=5,
                                   innerMarginHeight=5,
                                   preventOverride=False,
                                   selectCommand=self.change_tab,
                                   childResizable=True)
        maya.form_layout(self.form,
                        edit=True,
                        attachForm=((self.tab_display, 'top', 0),
                                    (self.tab_display, 'left', 0),
                                    (self.tab_display, 'bottom', 0),
                                    (self.tab_display, 'right', 0)))
        self.tabs = []
        maya.window(self.ui,
                    edit=True,
                    width=375,
                    height=575)
        maya.show(self.ui)
        maya.refresh()


    def is_logged_out(self):
        """Called when plug-in is logged out. Iterates through all UI tabs
        and sets them to logged-out state, and resets whether they have
        been loaded.
        Sets config/authentication tab as the display tab.
        """
        maya.tab_layout(self.tab_display, edit=True, selectTabIndex=1)
        for page in self.tabs:
            page.ready = False
            page.is_logged_out()

    def is_logged_in(self):
        """Called when the plug-in is authenticated. Sets the Submit tab as
        the display tab.
        """
        maya.tab_layout(self.tab_display, edit=True, selectTabIndex=2)
        self.tabs[0].is_logged_in()

    def change_tab(self, *args):
        """Called when a user clicks on a tab to display it.
        Initiates the loading of that tabs contents.
        """
        if self.base.config.auth:
            selected = maya.tab_layout(
                self.tab_display, query=True, selectTabIndex=True)
            selected_tab = self.tabs[selected-1]
            selected_tab.prepare()

    def select_tab(self, tab):
        """Select a specific tab for display.
        :param int tab: The index of the tab to display.
        """
        maya.tab_layout(self.tab_display, edit=True, selectTabIndex=tab)

    def selected_tab(self):
        """Get the index of the currently selected tab.
        :returns: The index (int) of the currently selected tab.
        """
        return maya.tab_layout(
            self.tab_display, query=True, selectTabIndex=True)

    def add_tab(self, content):
        """Add a new tab to the display layout.
        Content must have a ``page`` attribute as it's primary layout.

        :param content: This is called by any of the tab UI classes to
         add themselves to the plug-in UI.
        :type content: :class:`AzureBatchUI`


        """
        maya.form_layout(content.page, edit=True, parent=self.tab_display)
        self.tabs.append(content)
        new_layout = []
        for t in self.tabs:
            new_layout.append((str(t.page), t.label))
        new_layout = tuple(new_layout)
        maya.tab_layout(self.tab_display, edit=True, tabLabel=new_layout)
