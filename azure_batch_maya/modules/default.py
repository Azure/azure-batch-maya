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

from maya import cmds, mel


class AzureBatchRenderJob(object):

    def __init__(self):
        self._renderer = None
        self.label = "Renderer not supported"
        self.file_format = None

    @property
    def render_engine(self):
        return self._renderer

    @property
    def scene_name(self):
        scene = os.path.abspath(cmds.file(q=True, sn=True))
        if ((scene.endswith('.mb')) or (scene.endswith('.ma'))) and (os.path.exists(scene)):
            return str(os.path.normpath(scene))
        else:
            return ''

    @property
    def start_frame(self):
        animated = mel.eval("getAttr defaultRenderGlobals.animation")
        if animated:
            return int(mel.eval("getAttr defaultRenderGlobals.startFrame"))
        else:
            return int(cmds.currentTime(query=True))

    @property
    def end_frame(self):
        animated = mel.eval("getAttr defaultRenderGlobals.animation")
        if animated:
            return int(mel.eval("getAttr defaultRenderGlobals.endFrame"))
        else:
            return int(cmds.currentTime(query=True))

    @property
    def frame_step(self):
        return int(mel.eval("getAttr defaultRenderGlobals.byFrameStep"))

    def get_title(self):
        if self.scene_name == "":
            return "Untitled"
        else:
            return str(os.path.splitext(os.path.basename(self.scene_name))[0])

    def display_empty(self):
        cmds.text(label="")
        cmds.text(label="")

    def display_int(self, label, value, edit=True):
        cmds.text(label=label, align='right')
        if edit:
            return cmds.intField(value=value)
        else:
            return cmds.text(label=value, align='left')

    def display_string(self, label, value, edit=True):
        cmds.text(label=label, align='right')
        if edit:
            return cmds.textField(text=value)
        else:
            return cmds.text(label=value, align='left')

    def display_menu(self, label, options, selected):
        cmds.text(label=label, align='right')
        menu = cmds.optionMenu()
        for opt in options:
            cmds.menuItem(label=opt)
        cmds.setParent('..')
        cmds.optionMenu(menu, edit=True, select=selected)
        return menu

    def display_button(self, label, cmd):
        cmds.text(label="")
        return cmds.button(label=label, command=cmd, align='center')

    def display_file(self, label, value, cmd):
        cmds.text(label=label, align='right')
        selector = cmds.textFieldButtonGrp(
                        buttonLabel='Select',
                        adjustableColumn=1,
                        text=value)
        cmds.textFieldButtonGrp(selector, e=True, buttonCommand=lambda: cmd(selector)) 
        return selector

    def display_options(self, label, options):
        #TODO: Clean this up
        cmds.text(label=label, align='right')
        num_options = len(options)
        option_labels = [opt.keys()[0] for opt in options]
        if num_options == 2:
            return cmds.radioButtonGrp(
                    labelArray2=option_labels,
                    numberOfRadioButtons=2,
                    select=1,
                    vertical=True,
                    onCommand1=options[0].values()[0],
                    onCommand2=options[1].values()[0])
        if num_options == 3:
            return cmds.radioButtonGrp(
                    labelArray3=options.keys(),
                    numberOfRadioButtons=2,
                    select=1,
                    vertical=True,
                    onCommand1=options[0].values()[0],
                    onCommand2=options[1].values()[0],
                    onCommand3=options[2].values()[0])
        if num_options == 4:
            return cmds.radioButtonGrp(
                    labelArray4=options.keys(),
                    numberOfRadioButtons=2,
                    select=1,
                    vertical=True,
                    onCommand1=options[0].values()[0],
                    onCommand2=options[1].values()[0],
                    onCommand3=options[2].values()[0],
                    onCommand4=options[3].values()[0])

    def display(self, layout):
        self.module_layout = cmds.scrollLayout(
            horizontalScrollBarThickness=0,
            verticalScrollBarThickness=3,
            parent=layout,
            height=260)

        self.subLayout = cmds.rowColumnLayout(
            numberOfColumns=2,
            columnWidth=((1, 100),
                         (2, 200),),
            parent=self.module_layout,
            rowSpacing=(1, 10),
            rowOffset=((1, "top", 20),
                        (12, "top", 25),))
        self.display_string("Renderer:   ", self.label, edit=False)
        self.settings()

    def settings(self):
        pass

    def delete(self):
        cmds.deleteUI(self.module_layout)

    def render_enabled(self):
        return False

    def disable(self, enable):
        cmds.scrollLayout(self.module_layout, edit=True, enable=enable)
        
    def select_dir(self, *k):
        output = cmds.fileDialog2(fileMode=3)
        if not output:
            return None
        cmds.textFieldButtonGrp(k, edit=True, text=str(output[0]))


class AzureBatchRenderAssets(object):

    assets = []
    render_engine = ""

    def renderer_assets(self):
        return self.assets
