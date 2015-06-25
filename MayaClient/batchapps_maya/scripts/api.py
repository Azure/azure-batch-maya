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

try:
    from maya import cmds, mel, utils
    import maya.OpenMaya as om
    import maya.OpenMayaMPx as omp

except ImportError:
    print("No maya module found.")
    
import logging

class MayaAPI(object):

    @staticmethod
    def refresh():
        cmds.refresh()

    @staticmethod
    def mel(command):
        try:
            return mel.eval(command)
        except:
            return None

    @staticmethod
    def get_list(**kwargs):
        try:
            return cmds.ls(**kwargs)
        except:
            return []

    @staticmethod
    def get_attr(*args):
        try:
            return cmds.getAttr(*args)
        except:
            return ""

    @staticmethod
    def file(**kwargs):
        try:
            return cmds.file(**kwargs)
        except:
            return ""

    @staticmethod
    def file_select(**kwargs):
        return cmds.fileDialog2(dialogStyle=2, **kwargs)

    @staticmethod
    def error(message):
        log = logging.getLogger('BatchAppsMaya')
        log.warning(message)
        return cmds.confirmDialog(title="Error",
                                  message=message,
                                  messageAlign="left",
                                  button="OK",
                                  icon="critical")

    @staticmethod
    def warning(message):
        log = logging.getLogger('BatchAppsMaya')
        log.warning(message)
        return cmds.confirmDialog(title="Warning",
                                  message=message,
                                  messageAlign="left",
                                  button="OK",
                                  icon="warning")

    @staticmethod
    def workspace(*args, **kwargs):
        try:
            return cmds.workspace(*args, **kwargs)
        except:
            return None

    @staticmethod
    def dependency_nodes():
        return NodeIterator()

    @staticmethod
    def node_iterator():
        return om.MItDependencyNodes()

    @staticmethod
    def dependency_node(node):
        return om.MFnDependencyNode(node)

    @staticmethod
    def contentinfo_table():
        return omp.MExternalContentInfoTable()

    @staticmethod
    def delete_ui(*args, **kwargs):
        try:
            cmds.deleteUI(*args, **kwargs)
        except Exception as exp:
            print("Couldn't delete:", str(exp))

    @staticmethod
    def parent(parent='..'):
        cmds.setParent(parent)

    @staticmethod
    def text(*args, **kwargs):
        try:
            return cmds.text(*args, **kwargs)
        except:
            return None

    @staticmethod
    def text_field(*args, **kwargs):
        try:
            return cmds.textField(*args, **kwargs)
        except:
            return None

    @staticmethod
    def button(*args, **kwargs):
        try:
            return cmds.button(*args, **kwargs)
        except:
            return None

    @staticmethod
    def symbol_button(image, *args, **kwargs):
        try:
            return cmds.symbolButton(image=image, *args, **kwargs)
        except Exception as exp:
            print("symbolButton failed:",str(exp))
            return None

    @staticmethod
    def check_box(*args, **kwargs):
        try:
            return cmds.checkBox(*args, **kwargs)
        except Exception as exp:
            print("symbolCheck failed",str(exp))
            return None

    @staticmethod
    def symbol_check_box(*args, **kwargs):
        try:
            if kwargs.get('query') or kwargs.get('q'):
                return cmds.symbolCheckBox(*args, **kwargs)
            return cmds.symbolCheckBox(*args, onImage="precompExportChecked.png", offImage="precompExportUnchecked.png", **kwargs)
        except:
            return None

    @staticmethod
    def image(*args, **kwargs):
        try:
            return cmds.image(*args, **kwargs)
        except:
            return None

    @staticmethod
    def row_layout(*args, **kwargs):
        try:
            return cmds.columnLayout(*args, **kwargs)
        except:
            return None

    @staticmethod
    def col_layout(*args, **kwargs):
        try:
            return cmds.rowColumnLayout(*args, **kwargs)
        except Exception as exp:
            return None

    @staticmethod
    def frame_layout(*args, **kwargs):
        try:
            return cmds.frameLayout(*args, **kwargs)
        except Exception as e:
            return None

    @staticmethod
    def scroll_layout(*args, **kwargs):
        try:
            return cmds.scrollLayout(*args, **kwargs)
        except:
            return None

    @staticmethod
    def form_layout(*args, **kwargs):
        try:
            return cmds.formLayout(*args, **kwargs)
        except:
            return None

    @staticmethod
    def tab_layout(*args, **kwargs):
        try:
            return cmds.tabLayout(*args, **kwargs)
        except:
            return None

    @staticmethod
    def int_slider(*args, **kwargs):
        try:
            return cmds.intSliderGrp(*args, **kwargs)
        except:
            return None

    @staticmethod
    def menu(*args, **kwargs):
        try:
            return cmds.optionMenu(*args, **kwargs)
        except:
            return None

    @staticmethod
    def menu_option(*args, **kwargs):
        try:
            return cmds.menuItem(*args, **kwargs)
        except:
            return None

    @staticmethod
    def radio_group(*args, **kwargs):
        try:
            return cmds.radioButtonGrp(*args, **kwargs)
        except:
            return None

    @staticmethod
    def window(*args, **kwargs):
        try:
            return cmds.window(*args, **kwargs)
        except:
            return None

    @staticmethod
    def show(ui):
        try:
            cmds.showWindow(ui)
        except:
            pass

    @staticmethod
    def execute(*args):
        utils.executeDeferred(*args)

    @staticmethod
    def plugins(*args, **kwargs):
        try:
            return cmds.pluginInfo(*args, **kwargs)
        except:
            return None

class NodeIterator(object):

    def __init__(self):

        try:
            self._iter = MayaAPI.node_iterator()
        except:
            self._iter = iter([])

        self._current = None

    def get_references(self):
        dep_node = MayaAPI.dependency_node(self._current)
        assets = MayaReferences()

        self._iter.next()
        return assets.get_paths(dep_node)

    def is_done(self):
        try:       
            is_complete = self._iter.isDone()

            if not is_complete:
                self._current  = self._iter.thisNode()
            
            return is_complete

        except Exception as exp:
            True

class MayaCallbacks(object):

    @staticmethod
    def after_save(func):
        return om.MSceneMessage.addCallback(om.MSceneMessage.kAfterSave, func)

    @staticmethod
    def after_new(func):
        return om.MSceneMessage.addCallback(om.MSceneMessage.kAfterNew, func)

    @staticmethod
    def after_open(func):
        return om.MSceneMessage.addCallback(om.MSceneMessage.kAfterFileRead, func)

    @staticmethod
    def remove(callback):
        om.MSceneMessage.removeCallback(callback)

class MayaReferences(object):

    def __init__(self):
        self._table = MayaAPI.contentinfo_table()

    def get_paths(self, node):
        node.getExternalContent(self._table)
        paths = []

        for i in range(self._table.length()):
            _path = []
            _node = ""
            _role = []
            self._table.getEntryByIndex(i, _path, _node, _role)
            if _path:
                if '.' in _path[0]:
                    paths.append(_path[0])

        return paths

