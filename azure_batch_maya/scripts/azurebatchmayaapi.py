# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

try:
    from maya import cmds, mel, utils
    import maya.OpenMaya as om
    import maya.OpenMayaMPx as omp
except ImportError:
    print("No maya module found.")
import os
import logging
LOG = logging.getLogger('AzureBatchMaya')


class MayaAPI(object):

    @staticmethod
    def refresh():
        cmds.refresh()

    @staticmethod
    def mel(command):
        try:
            return mel.eval(command)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'mel': {0}".format(exp).strip())
            return None

    @staticmethod
    def get_list(**kwargs):
        try:
            return cmds.ls(**kwargs)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'get_list': {0}".format(exp).strip())
            return []

    @staticmethod
    def get_attr(*args):
        try:
            return cmds.getAttr(*args)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'get_attr': {0}".format(exp).strip())
            return ""

    @staticmethod
    def file(**kwargs):
        try:
            return cmds.file(**kwargs)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'file': {0}".format(exp).strip())
            return ""

    @staticmethod
    def reference(*args, **kwargs):
        try:
            return cmds.referenceQuery(*args, **kwargs)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'reference': {0}".format(exp).strip())
            return None

    @staticmethod
    def animated():
        return MayaAPI.get_attr("defaultRenderGlobals.animation")

    @staticmethod
    def start_frame():
        if MayaAPI.animated():
            return int(MayaAPI.get_attr("defaultRenderGlobals.startFrame"))
        else:
            return int(cmds.currentTime(query=True))

    @staticmethod
    def end_frame():
        animated = mel.eval("getAttr defaultRenderGlobals.animation")
        if MayaAPI.animated():
            return int(MayaAPI.get_attr("defaultRenderGlobals.endFrame"))
        else:
            return int(cmds.currentTime(query=True))

    @staticmethod
    def frame_step():
        return int(mel.eval("getAttr defaultRenderGlobals.byFrameStep"))

    @staticmethod
    def file_select(**kwargs):
        return cmds.fileDialog2(dialogStyle=2, **kwargs)

    @staticmethod
    def error(message):
        LOG.warning(message)
        return cmds.confirmDialog(title="Error",
                                  message=message,
                                  messageAlign="left",
                                  button="OK",
                                  icon="critical")

    @staticmethod
    def warning(message):
        LOG.warning(message)
        return cmds.confirmDialog(title="Warning",
                                  message=message,
                                  messageAlign="left",
                                  button="OK",
                                  icon="warning")

    @staticmethod
    def info(message):
        LOG.info(message)
        return cmds.confirmDialog(title="",
                                  message=message,
                                  messageAlign="left",
                                  button="OK",
                                  icon="information")

    @staticmethod
    def confirm(message, options):
        LOG.info(message)
        return cmds.confirmDialog(title="",
                                  message=message,
                                  messageAlign="left",
                                  button=options,
                                  defaultButton=options[-1],
                                  cancelButton=options[-1],
                                  dismissString=options[-1],
                                  icon="information")

    @staticmethod
    def workspace(*args, **kwargs):
        try:
            return cmds.workspace(*args, **kwargs)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'workspace': {0}".format(exp).strip())
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
    def node_attribute(node, dep_node, attr):
        attr_obj = dep_node.attribute(attr)
        return om.MPlug(node, attr_obj)

    @staticmethod
    def contentinfo_table():
        return omp.MExternalContentInfoTable()

    @staticmethod
    def delete_ui(*args, **kwargs):

        def isListEmpty(inList):
            if isinstance(inList, list): # Is a list
                return all( map(isListEmpty, inList) )
            return False # Not a list

        try:
            argsNoFalsies = [x for x in args if x]
            if isListEmpty(argsNoFalsies):
                return      # cmds.deleteUI throws if called with an empty list
            cmds.deleteUI(*argsNoFalsies, **kwargs)
        except Exception as exp:
            if exp.message.endswith('not found.\n'):
                return    # ignore exceptions from attempting to delete an object which is already deleted
            LOG.debug("MayaAPI exception in 'delete_ui': {0}".format(exp).strip())

    @staticmethod
    def parent(parent='..'):
        cmds.setParent(parent)

    @staticmethod
    def text(*args, **kwargs):
        try:
            return cmds.text(*args, **kwargs)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'text': {0}".format(exp).strip())
            return None

    @staticmethod
    def text_field(*args, **kwargs):
        try:
            return cmds.textField(*args, **kwargs)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'text_field': {0}".format(exp).strip())
            return None

    @staticmethod
    def button(*args, **kwargs):
        try:
            return cmds.button(*args, **kwargs)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'button': {0}".format(exp).strip())
            return None

    @staticmethod
    def symbol_button(*args, **kwargs):
        try:
            return cmds.symbolButton(*args, **kwargs)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'symbol_button': {0}".format(exp).strip())
            return None

    @staticmethod
    def icon_button(*args, **kwargs):
        try:
            return cmds.iconTextButton(*args, **kwargs)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'icon_button': {0}".format(exp).strip())
            return None

    @staticmethod
    def check_box(*args, **kwargs):
        try:
            return cmds.checkBox(*args, **kwargs)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'check_box': {0}".format(exp).strip())
            return None

    @staticmethod
    def symbol_check_box(*args, **kwargs):
        try:
            if kwargs.get('query') or kwargs.get('q'):
                return cmds.symbolCheckBox(*args, **kwargs)
            return cmds.symbolCheckBox(*args,
                                       onImage="precompExportChecked.png",
                                       offImage="precompExportUnchecked.png",
                                       **kwargs)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'symbol_check_box': {0}".format(exp).strip())
            return None

    @staticmethod
    def image(*args, **kwargs):
        try:
            return cmds.image(*args, **kwargs)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'image': {0}".format(exp).strip())
            return None

    @staticmethod
    def row_layout(*args, **kwargs):
        try:
            return cmds.columnLayout(*args, **kwargs)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'row_layout': {0}".format(exp).strip())
            return None

    @staticmethod
    def row(*args, **kwargs):
        try:
            return cmds.rowLayout(*args, **kwargs)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'row_': {0}".format(exp).strip())
            return None

    @staticmethod
    def col_layout(*args, **kwargs):
        try:
            return cmds.rowColumnLayout(*args, **kwargs)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'col_layout': {0}".format(exp).strip())
            return None

    @staticmethod
    def frame_layout(*args, **kwargs):
        try:
            return cmds.frameLayout(*args, **kwargs)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'frame_layout': {0}".format(exp).strip())
            return None

    @staticmethod
    def scroll_layout(*args, **kwargs):
        try:
            return cmds.scrollLayout(*args, **kwargs)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'scroll_layout': {0}".format(exp).strip())
            return None

    @staticmethod
    def form_layout(*args, **kwargs):
        try:
            return cmds.formLayout(*args, **kwargs)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'form_layout': {0}".format(exp).strip())
            return None

    @staticmethod
    def tab_layout(*args, **kwargs):
        try:
            return cmds.tabLayout(*args, **kwargs)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'tab_layout': {0}".format(exp).strip())
            return None

    @staticmethod
    def grid_layout(*args, **kwargs):
        try:
            return cmds.gridLayout (*args, **kwargs)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'grid_layout': {0}".format(exp).strip())
            return None

    @staticmethod
    def int_slider(*args, **kwargs):
        try:
            return cmds.intSliderGrp(*args, **kwargs)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'int_slider': {0}".format(exp).strip())
            return None

    @staticmethod
    def int_field(*args, **kwargs):
        try:
            return cmds.intField(*args, **kwargs)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'int_field': {0}".format(exp).strip())
            return None

    @staticmethod
    def popup_menu(*args, **kwargs):
        try:
            return cmds.popupMenu(*args, **kwargs)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'popup_menu': {0}".format(exp).strip())
            return None

    @staticmethod
    def menu(*args, **kwargs):
        try:
            return cmds.optionMenu(*args, **kwargs)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'menu': {0}".format(exp).strip())
            return None

    @staticmethod
    def menu_option(*args, **kwargs):
        try:
            return cmds.menuItem(*args, **kwargs)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'menu_option': {0}".format(exp).strip())
            return None

    @staticmethod
    def radio_group(*args, **kwargs):
        try:
            return cmds.radioButtonGrp(*args, **kwargs)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'radio_group': {0}".format(exp).strip())
            return None

    @staticmethod
    def table(*args, **kwargs):
        #note in order to have a horizontal scroll bar displayable on resize, the table must contain at least 2 columns
        try:
            return cmds.scriptTable(*args, **kwargs)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'table': {0}".format(exp).strip())
            return None

    @staticmethod
    def progress_bar(*args, **kwargs):
        try:
            return cmds.progressBar(*args, **kwargs)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'progress_bar': {0}".format(exp).strip())
            return None

    @staticmethod
    def window(*args, **kwargs):
        try:
            return cmds.window(*args, **kwargs)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'window': {0}".format(exp).strip())
            return None

    @staticmethod
    def show(ui):
        try:
            cmds.showWindow(ui)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'show': {0}".format(exp).strip())

    @staticmethod
    def execute(*args, **kwargs):
        cmds.evalDeferred(*args, **kwargs)

    @staticmethod
    def execute_in_main_thread(*args, **kwargs):
        return utils.executeInMainThreadWithResult(*args, **kwargs)

    @staticmethod
    def plugins(*args, **kwargs):
        try:
            return cmds.pluginInfo(*args, **kwargs)
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'plugins': {0}".format(exp).strip())
            return None

    @staticmethod
    def prefs_dir():
        return cmds.internalVar(userPrefDir=True)

    @staticmethod
    def script_dir():
        return cmds.internalVar(userScriptDir=True)

    @staticmethod
    def about(*args, **kwargs):
        return cmds.about(*args, **kwargs)


class NodeIterator(object):

    def __init__(self):
        try:
            self._iter = MayaAPI.node_iterator()
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'NodeIterator': {0}".format(exp).strip())
            self._iter = iter([])
        self._current = None

    def get_references(self):
        assets = MayaReferences(self._current)
        self._iter.next()
        return assets.get_paths()

    def is_done(self):
        try:
            is_complete = self._iter.isDone()
            if not is_complete:
                self._current  = self._iter.thisNode()
            return is_complete
        except Exception as exp:
            LOG.debug("MayaAPI exception in 'NodeIterator': {0}".format(exp).strip())
            True

class MayaCallbacks(object):
    """Add callbacks to Maya's event handlers for various scene file
    events, including saving, loading, creating etc.
    """

    @staticmethod
    def after_save(func):
        return om.MSceneMessage.addCallback(om.MSceneMessage.kAfterSave, func)

    @staticmethod
    def after_new(func):
        return om.MSceneMessage.addCallback(om.MSceneMessage.kAfterNew, func)

    @staticmethod
    def after_open(func):
        return om.MSceneMessage.addCallback(om.MSceneMessage.kAfterOpen, func)

    @staticmethod
    def after_read(func):
        return om.MSceneMessage.addCallback(om.MSceneMessage.kAfterFileRead, func)

    @staticmethod
    def remove(callback):
        om.MSceneMessage.removeCallback(callback)


class MayaReferences(object):

    def __init__(self, node):
        self._node = node
        self._dep_node = MayaAPI.dependency_node(node)
        self._table = MayaAPI.contentinfo_table()

    def get_paths(self):
        self._dep_node.getExternalContent(self._table)
        paths = []
        for i in range(self._table.length()):
            _path = []
            _node = ""
            _role = []
            self._table.getEntryByIndex(i, _path, _node, _role)
            if _path and '.' in _path[0]:
                paths.append(_path[0])
        token_ref = self.token_paths()
        if token_ref:
            paths.append(token_ref)
        return paths

    def token_paths(self):
        try:
            pattern = MayaAPI.node_attribute(
                self._node, self._dep_node, "computedFileTextureNamePattern")
            pattern = str(pattern.asString())

            if "<udim>" in pattern.lower():
                LOG.debug("Found UDIM reference: {0}".format(pattern))
                pattern = pattern.replace("<UDIM>", "[0-9][0-9][0-9][0-9]")
                pattern = pattern.replace("<udim>", "[0-9][0-9][0-9][0-9]")
                return os.path.normpath(pattern)

            elif "u<u>_v<v>" in pattern.lower():
                LOG.debug("Found UV reference: {0}".format(pattern))
                pattern = pattern.replace("<u>", "*")
                pattern = pattern.replace("<v>", "*")
                pattern = pattern.replace("<f>", "*")
                pattern = pattern.replace("<U>", "*")
                pattern = pattern.replace("<V>", "*")
                pattern = pattern.replace("<F>", "*")
                return os.path.normpath(pattern)

            elif "<tile>" in pattern.lower():
                LOG.debug("Found tile reference: {0}".format(pattern))
                pattern = pattern.replace("<tile>", "_u*_v*")
                pattern = pattern.replace("<TILE>", "_u*_v*")
                return os.path.normpath(pattern)

        except Exception as exp:
            return None
