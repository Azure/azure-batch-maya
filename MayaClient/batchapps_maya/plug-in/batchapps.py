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

from maya import mel
from maya import cmds

from maya.OpenMayaMPx import MFnPlugin
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx

import os
import sys
import inspect


VERSION = "0.3.1"

cmd_name = "BatchApps"
fMayaExitingCB = None


class BatchAppsSetup(OpenMayaMPx.MPxCommand):

    def __init__(self):
        OpenMayaMPx.MPxCommand.__init__(self)

    @staticmethod
    def clean(p):
        if os.sep == "\\":
            return p.replace(os.sep, "\\\\")
        return p

    @staticmethod
    def create_modfile(p, plugin_path):
        try:
            modfile = os.path.join(p, "batchapps.mod")
            with open(modfile, 'w') as mod:
                mod.write("+ BatchApps {0} {1}\n".format(VERSION, plugin_path))
                mod.write("MAYA_PLUG_IN_PATH+={0}\n".format(os.path.join(plugin_path, "plug-in")))
                mod.write("MAYA_SCRIPT_PATH+:=mel\n")
                mod.write("BATCHAPPS_ICONS:=icons\n")
                mod.write("BATCHAPPS_SCRIPTS:=scripts\n")
                mod.write("BATCHAPPS_SCRIPTS+:=scripts/ui\n")
                mod.write("BATCHAPPS_MODULES:=modules")

            print("Successfully created mod file at %s" % p)
            print("Setting environment variables for current session.")
            mel.eval("""putenv "BATCHAPPS_SCRIPTS" "{0};{1};" """.format(
                BatchAppsSetup.clean(os.path.join(plugin_path, "scripts")),
                BatchAppsSetup.clean(os.path.join(plugin_path, "scripts", "ui"))))

            return True

        except Exception as e:
            print(str(e))
            print("Couldn't create mod file at %s" % p)
            return False

    @staticmethod
    def find_modules_locations(plugin_path):
        modulepaths = mel.eval("""getenv "MAYA_MODULE_PATH" """).split(os.pathsep)
        modulepaths.reverse()

        for p in modulepaths:
            if not os.path.isdir(p):

                try:
                    os.makedirs(p)
                except:
                    print("Module directory doesn't exist, and cannot create it: %s" % p)
         
            if BatchAppsSetup.create_modfile(p, plugin_path):
                return True

        return False

    @staticmethod
    def find_env_location(plugin_path):
        maya_env = os.path.join(os.path.normpath(os.environ['MAYA_APP_DIR']), "Maya.env")

        if not os.path.isfile(maya_env):
            maya_env = os.path.normpath(os.path.join(mel.eval("about -preferences"), "Maya.env"))

        return BatchAppsSetup.add_modulepath_to_env(plugin_path, maya_env)

    @staticmethod
    def add_modulepath_to_env(plugin_path, env_path):
        plugin_mods = os.path.join(plugin_path, "modules")
        open_format = 'a' if os.path.exists(env_path) else 'w'

        try:
            with open(env_path, open_format) as modfile:

                if open_format == 'a' and modfile.tell() != 0:
                    modfile.seek(-1, os.SEEK_END)
                    next_char = modfile.read(1)

                    if next_char != '\n':
                        modfile.write('\n')

                if os.pathsep == ';':
                    modfile.write("MAYA_MODULE_PATH=%MAYA_MODULE_PATH%;{0}".format(plugin_mods))
                else:
                    modfile.write("MAYA_MODULE_PATH=$MAYA_MODULE_PATH:{0}".format(plugin_mods))

            return BatchAppsSetup.create_modfile(plugin_mods, plugin_path)
        except Exception as exp:
            print("Couldn't create new maya env file: %s" % env_path)
            return False

    @staticmethod
    def remove_environment():
        modulepaths = mel.eval("""getenv "MAYA_MODULE_PATH" """).split(os.pathsep)
        modulepaths.reverse()

        for p in modulepaths:
            modfile = os.path.join(p, "batchapps.mod")

            if os.path.exists(modfile):
                try:
                    os.remove(modfile)

                except:
                    print("Found BatchApps mod file, but couldn't delete. ", modfile)

    @staticmethod
    def set_environment(p):
        srcpath = os.path.join(p, "scripts")
        icnpath = os.path.join(p, "icons")
        melpath = os.path.join(p, "mel")
        modpath = os.path.join(p, "modules")
        sys.path.append(modpath)
        sys.path.append(srcpath)
        sys.path.append(os.path.join(srcpath, "ui"))
        #sys.path.append(os.path.join(srcpath, "props"))

        script_dirs = mel.eval("""getenv "MAYA_SCRIPT_PATH" """) + os.pathsep
        mel.eval("""putenv "MAYA_SCRIPT_PATH" ("{0}" + "{1}") """.format(script_dirs, BatchAppsSetup.clean(melpath)))
        mel.eval("""putenv "BATCHAPPS_ICONS" "{0}" """.format(BatchAppsSetup.clean(icnpath)))
        mel.eval("""putenv "BATCHAPPS_MODULES" "{0}" """.format(BatchAppsSetup.clean(modpath)))

        print("Attempting to create mod file under MAYA_MODULE_PATH")
        mods = BatchAppsSetup.find_modules_locations(p)

        if not mods:
            print("Attempting to add custom module path to Maya.env")
            mods = BatchAppsSetup.find_env_location(p)

        if not mods:
            print("Failed to setup BatchApps mod file")

        return mel.eval("""getenv "MAYA_MODULE_PATH" """) + os.pathsep

def cmd_creator():
    return OpenMayaMPx.asMPxPtr(BatchAppsSetup())

def setup_module():
    current_file = inspect.getfile(inspect.currentframe())
    current_dir = os.path.dirname(os.path.abspath(current_file))
    plugin_path =  os.path.split(current_dir)[0] + os.sep
    BatchAppsSetup.set_environment(plugin_path)

def get_usershelf_dir(filename):
    shelfDirs = mel.eval("internalVar -userShelfDir").split(os.pathsep)

    for d in shelfDirs:

        if (d.startswith(mel.eval("internalVar -userPrefDir")) and (d.endswith("/prefs/shelves/"))):
            melPath = os.path.join(os.path.normpath(d), filename)

            if os.path.exists(melPath):
                return melPath

    return os.path.normpath(os.path.join(mel.eval("about -preferences"), "prefs", "shelves", filename))

def remove_ui(clientData):
    try:
        try:
            mel.eval("""deleteUI -layout('BatchApps')""")

        except:
            print("Couldn't delete shelf")

        melPath = get_usershelf_dir("shelf_BatchApps.mel")

        if os.path.exists("{0}.deleted".format(melPath)):
            os.remove("{0}.deleted".format(melPath))

        os.rename(melPath, "{0}.deleted".format(melPath))

    except Exception as e:
        print("Failed to load", (str(e)))

def initializePlugin(obj):
    print("Initializing Batch Apps plug-in")

    plugin = OpenMayaMPx.MFnPlugin(obj, "me", "1.0", "Any")
    plugin.registerCommand(cmd_name, cmd_creator)

    try:
        if (mel.eval("""shelfLayout -exists "BatchApps" """) == 0):
            mel.eval('addNewShelfTab %s' % "BatchApps")
            mel.eval("""source "create_shelf.mel" """)

        melPath = get_usershelf_dir("shelf_BatchApps.mel")
        if os.path.exists("{0}.deleted".format(melPath)):
            os.remove("{0}.deleted".format(melPath))

        os.rename(melPath, "{0}.deleted".format(melPath))

    except:
        print("Couldn't add shelf")

    # Add callback to clean up UI when Maya exits
    global fMayaExitingCB
    fMayaExitingCB = OpenMaya.MSceneMessage.addCallback(OpenMaya.MSceneMessage.kMayaExiting, remove_ui)

def uninitializePlugin(obj):
    print("Removing BatchApps plug-in")

    plugin = MFnPlugin(obj)
    plugin.deregisterCommand(cmd_name)

    try:
        mel.eval('deleteShelfTab %s' % "BatchApps")

    except:
        print("Couldn't delete shelf")

    global fMayaExitingCB
    if (fMayaExitingCB is not None):
        OpenMaya.MSceneMessage.removeCallback(fMayaExitingCB)

    if cmds.window("BatchApps", exists=1):
        cmds.deleteUI("BatchApps")

    BatchAppsSetup.remove_environment()
    print("Finished clearing up all BatchApps components")

try:
    sys.path.extend(os.environ["BATCHAPPS_SCRIPTS"].split(os.pathsep))
    sys.path.append(os.environ['BATCHAPPS_MODULES'])

except KeyError as e:
    print("Couldn't find BatchApps environment, setting up now...")
    setup_module()
