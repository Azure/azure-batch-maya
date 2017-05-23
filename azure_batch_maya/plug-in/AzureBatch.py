# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import urllib
import os
import tarfile
import shutil
import sys
import zipfile
import warnings
import importlib
import tempfile
import inspect
import glob
import webbrowser
import subprocess
from distutils.version import StrictVersion

from maya import mel
from maya import cmds

from maya.OpenMayaMPx import MFnPlugin
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx

warnings.simplefilter('ignore')

INSTALL_DIR = os.path.normpath(
    os.path.join(cmds.internalVar(userScriptDir=True), 'azure-batch-libs'))
sys.path.append(INSTALL_DIR)

REQUIREMENTS = [
    "pathlib==1.0.1",
]

NAMESPACE_PACAKGES = [
    "azure-mgmt-batch==4.0.0",
    "azure-mgmt-storage==1.0.0",
    "azure-common==1.1.5",
    "azure-batch==3.0.0",
    "azure-storage==0.32.0",
]

VERSION = "0.9.0"
EULA_PREF = "AzureBatch_EULA"
SHELF_FILE = "shelf_AzureBatch.mel"
cmd_name = "AzureBatch"
fMayaExitingCB = None
os.environ["AZUREBATCH_VERSION"] = VERSION


def eula_prompt():
    """Open prompt for terms and conditions."""
    current_file = inspect.getfile(inspect.currentframe())
    current_dir = os.path.dirname(os.path.abspath(current_file))
    eula = os.path.join(current_dir, "EULA.html")
    form = cmds.setParent(q=True)
    cmds.formLayout(form, e=True, width=500)
    heading = cmds.text(
        l='Maya Cloud Rendering License Agreement', font="boldLabelFont")
    text = cmds.text(l="By loading this plug-in you are agreeing to "
                        "the following terms and conditions.")
    if not os.path.exists(eula):
        raise RuntimeError("EULA notice not found at {0}".format(eula))

    with open(eula, "rb") as eula_text:
        html = eula_text.read()
        unicode = html.decode("windows-1252")
        encoded_str = unicode.encode("ascii", "xmlcharrefreplace")
        read = cmds.scrollField(editable=False, wordWrap=True, height=300,
                                text=unicode, backgroundColor=(1.0,1.0,1.0))
    agree = cmds.button(l='Agree', c='maya.cmds.layoutDialog( dismiss="Agree" )' )
    disagree = cmds.button(l='Disagree', c='maya.cmds.layoutDialog( dismiss="Disagree" )' )
    cmds.formLayout(form, edit=True,
                    attachForm=[(heading, 'top', 10), (heading, 'left', 10),
                                (heading, 'right', 10), (read, 'left', 10),
                                (read, 'right', 10), (text, 'left', 10),
                                (text, 'right', 10), (agree, 'left', 10),
                                (agree, 'bottom', 10), (disagree, 'right', 10),
                                (disagree, 'bottom', 10)],
                    attachNone=[(text, 'bottom'), (read, 'bottom')],
                    attachControl=[(text, 'top', 10, heading),
                                    (read, 'top', 10, text),
                                    (agree, 'top', 50, read),
                                    (disagree, 'top', 50, read)],
                    attachPosition=[(agree, 'right', 5, 50),
                                    (disagree, 'left', 5, 50)])


class AzureBatchSetup(OpenMayaMPx.MPxCommand):
    """Plug-in Setup Module."""

    def __init__(self):
        OpenMayaMPx.MPxCommand.__init__(self)

    @staticmethod
    def clean(path):
        """Modify Windows paths for writing to files.
        :param str path: The path to clean.
        """
        if os.sep == "\\":
            return path.replace(os.sep, "\\\\")
        return path

    @staticmethod
    def create_modfile(mod_path, plugin_path):
        """Write all environment variables to mod file at a given
        location.

        :param str mod_path: The module directory path in which we'll attempt
         to create the mod file.
        :param str plugin_path: The directory where the plug-in files
          currently reside.
        :returns: True if the mod file was successfully created, else
         False.
        """
        try:
            modfile = os.path.join(mod_path, "AzureBatch.mod")
            with open(modfile, 'w') as mod:
                mod.write("+ AzureBatch {0} {1}\n".format(
                    VERSION, plugin_path))
                mod.write("MAYA_PLUG_IN_PATH+={0}\n".format(
                    os.path.join(plugin_path, "plug-in")))
                mod.write("MAYA_SCRIPT_PATH+:=mel\n")
                mod.write("AZUREBATCH_ICONS:=icons\n")
                mod.write("AZUREBATCH_TEMPLATES:=templates\n")
                mod.write("AZUREBATCH_SCRIPTS:=scripts\n")
                mod.write("AZUREBATCH_SCRIPTS+:=scripts/ui\n")
                mod.write("AZUREBATCH_TOOLS:=scripts/tools\n")
                mod.write("AZUREBATCH_MODULES:=modules")

            print("Successfully created mod file at %s" % mod_path)
            print("Setting environment variables for current session.")
            os.environ["AZUREBATCH_SCRIPTS"] = "{0};{1};".format(
                AzureBatchSetup.clean(os.path.join(plugin_path,
                                                  "scripts")),
                AzureBatchSetup.clean(os.path.join(plugin_path,
                                                  "scripts", "ui")))
            return True
        except Exception as err:
            print(str(err))
            print("Couldn't create mod file at %s" % mod_path)
            return False

    @staticmethod
    def find_modules_locations(plugin_path):
        """Iterate through paths in MAYA_MODULE_PATH to find appropriate
        directory to create mod file.
        Attempts to create a module directory at the specified path if
        it doesn't already exist.
        
        :param str plugin_path: Path where the plug-in files currently
         reside.
        :returns: True if a directory is found and mod file successfully
         created there, else False.
        """
        modulepaths = os.environ["MAYA_MODULE_PATH"].split(os.pathsep)
        modulepaths.reverse()
        for path in modulepaths:
            if not os.path.isdir(path):
                try:
                    os.makedirs(p)
                except:
                    print("Module directory doesn't exist, "
                          "and cannot create it: %s" % path)
                    continue
            if AzureBatchSetup.create_modfile(path, plugin_path):
                return True
        return False

    @staticmethod
    def find_env_location(plugin_path):
        """Find directory of Maya.env files.

        :param str plugin_path: Path where the plug-in files currently
         reside.
        :returns: True if a custom module path is successfully added to
         Maya.env, else False.
        """
        maya_app_dir = os.path.normpath(os.environ.get('MAYA_APP_DIR', ""))
        maya_env = os.path.join(maya_app_dir, "Maya.env")
        if not os.path.isfile(maya_env):
            maya_env = os.path.join(mel.eval("about -preferences"), "Maya.env")
            maya_env = os.path.normpath(maya_env)
        return AzureBatchSetup.add_modulepath_to_env(plugin_path, maya_env)

    @staticmethod
    def add_modulepath_to_env(plugin_path, env_path):
        """Add a new entry for MAYA_MODULE_PATH to Maya.env and create mod
        file at this path.

        :param str plugin_path: Path where the plug-in files currently
         reside.
        :param str env_path: Path to Maya.env.
        :returns: True if Maya.env configured and mod file created,
         else False.
        """
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
                    modfile.write(
                        "MAYA_MODULE_PATH=%MAYA_MODULE_PATH%;{0}".format(
                            plugin_mods))
                else:
                    modfile.write(
                        "MAYA_MODULE_PATH=$MAYA_MODULE_PATH:{0}".format(
                            plugin_mods))
            return AzureBatchSetup.create_modfile(plugin_mods, plugin_path)
        except Exception as exp:
            print("Couldn't create new maya env file: %s" % env_path)
            return False

    @staticmethod
    def remove_environment():
        """Iterate through paths in MAYA_MODULE_PATH to find and remove
        any mod files.
        """
        modulepaths = os.environ.get("MAYA_MODULE_PATH", "").split(os.pathsep)
        modulepaths.reverse()
        for p in modulepaths:
            modfile = os.path.join(p, "AzureBatch.mod")
            if os.path.exists(modfile):
                try:
                    print("Removing mod file from {0}".format(modfile))
                    os.remove(modfile)
                except:
                    print("Found AzureBatch mod file {0}, but "
                          "couldn't delete.".format(modfile))
        message = "Remove installed Python dependencies?"
        del_python = cmds.confirmDialog(
            title='Azure Batch', message=message, button=['Yes','No'],
            defaultButton='No', dismissString='No')

        if del_python == 'Yes':
            try:
                print("Removing Python dependencies: {0}".format(INSTALL_DIR))
                shutil.rmtree(INSTALL_DIR)
            except:
                print("Couldn't remove {0}".format(INSTALL_DIR))

    @staticmethod
    def set_environment(plugin_path):
        """Set environment variables for current session, if they haven't
        been set by a mod file on startup. (I.e. after first installed)
        Attempt to create mod file for future sessions.

        :param str plugin_path: The directory where the plug-in files
          currently reside.
        """
        srcpath = os.path.join(plugin_path, "scripts")
        icnpath = os.path.join(plugin_path, "icons")
        melpath = os.path.join(plugin_path, "mel")
        modpath = os.path.join(plugin_path, "modules")
        tplpath = os.path.join(plugin_path, "templates")
        tolpath = os.path.join(plugin_path, "scripts", "tools")
        sys.path.append(modpath)
        sys.path.append(srcpath)
        sys.path.append(os.path.join(srcpath, "ui"))

        script_dirs = os.environ["MAYA_SCRIPT_PATH"] + os.pathsep
        os.environ["AZUREBATCH_ICONS"] = AzureBatchSetup.clean(icnpath)
        os.environ["AZUREBATCH_MODULES"] = AzureBatchSetup.clean(modpath)
        os.environ["AZUREBATCH_TEMPLATES"] = AzureBatchSetup.clean(tplpath)
        os.environ["AZUREBATCH_TOOLS"] = AzureBatchSetup.clean(tolpath)
        os.environ["MAYA_SCRIPT_PATH"] = script_dirs + \
            AzureBatchSetup.clean(melpath)
        print("Attempting to create mod file under MAYA_MODULE_PATH")
        mods = AzureBatchSetup.find_modules_locations(plugin_path)

        if not mods:
            print("Attempting to add custom module path to Maya.env")
            mods = AzureBatchSetup.find_env_location(plugin_path)
        if not mods:
            print("Failed to setup AzureBatch mod file")
        return  os.environ["MAYA_MODULE_PATH"] + os.pathsep


def cmd_creator():
    """Create set up command"""
    return OpenMayaMPx.asMPxPtr(AzureBatchSetup())


def setup_module():
    """Set up module environment"""
    current_file = inspect.getfile(inspect.currentframe())
    current_dir = os.path.dirname(os.path.abspath(current_file))
    plugin_path =  os.path.split(current_dir)[0] + os.sep
    AzureBatchSetup.set_environment(plugin_path)


def get_usershelf_dir():
    """Get directory of saved shelf preferences."""
    shelf_dirs = mel.eval("internalVar -userShelfDir").split(os.pathsep)
    for dir in shelf_dirs:
        if (dir.startswith(mel.eval("internalVar -userPrefDir")) and \
            (dir.endswith("/prefs/shelves/"))):
            melPath = os.path.join(os.path.normpath(dir), SHELF_FILE)
            if os.path.exists(melPath):
                return melPath

    prefs = mel.eval("about -preferences")
    pref_dir = os.path.join(prefs, "prefs", "shelves", SHELF_FILE)
    return os.path.normpath(pref_dir)


def remove_ui(clientData):
    """Remove shelf preferences if plug-in deselected."""
    try:
        try:
            mel.eval("""deleteUI -layout('AzureBatch')""")
        except:
            print("Couldn't delete shelf")
        melPath = get_usershelf_dir()
        if os.path.exists("{0}.deleted".format(melPath)):
            os.remove("{0}.deleted".format(melPath))
        os.rename(melPath, "{0}.deleted".format(melPath))
    except Exception as e:
        print("Failed to load", (str(e)))


def dependency_installed(package):
    """Check if the specified package is installed and up-to-date.
    :param str package: A pip-formatted package reference.
    """
    try:
        package_ref = package.split('==')
        module = importlib.import_module(package_ref[0].replace('-', '.'))
        if hasattr(module, '__version__') and len(package_ref) > 1:
            if StrictVersion(package_ref[1]) > StrictVersion(getattr(module, '__version__')):
                raise ImportError("Installed package out of date")
    except ImportError:
        print("Unable to load {}".format(package))
        return False
    else:
        return True


def install_pkg(package):
    """Install the specified package by shelling out to pip.
    :param str package: A pip-formatted package reference.

    TODO: Check if there's a better way to bypass the verification error.
    TODO: Check if this works for package upgrades
    """
    pip_cmds = ['mayapy', os.path.join(INSTALL_DIR, 'pip'), 
                'install', package, 
                '--target', INSTALL_DIR,
                '--index-url', 'http://pypi.python.org/simple/',
                '--trusted-host', 'pypi.python.org']
    print(pip_cmds)
    installer = subprocess.Popen(pip_cmds)
    installer.wait()
    if installer.returncode != 0:
        raise RuntimeError("Failed to install package: {}".format(package))


def install_namespace_pkg(package, namespace):
    """Azure packages have issues installing one by one as they don't
    unpackage correctly into the namespace directory. So we have to install
    to a temp directory and move it to the right place.

    :param str package: A pip-formatted package reference.
    :param str namespace: The package namespace to unpack to.
    """
    temp_target = os.path.join(INSTALL_DIR, 'temp-target')
    pip_cmds = ['mayapy', os.path.join(INSTALL_DIR, 'pip'),
                'install', package, 
                '--no-deps',
                '--target', temp_target,
                '--index-url', 'http://pypi.python.org/simple/',
                '--trusted-host', 'pypi.python.org']
    installer = subprocess.Popen(pip_cmds)
    installer.wait()
    if installer.returncode == 0:
        try:
            shutil.copytree(os.path.join(temp_target, namespace), os.path.join(INSTALL_DIR, namespace))
        except Exception as e:
            print(e)
        try:
            shutil.rmtree(temp_target)
        except Exception as e:
            print(e)


def initializePlugin(obj):
    """Initialize Plug-in"""
    print("Initializing Azure Batch plug-in")
    existing = cmds.optionVar(exists=EULA_PREF)
    if not existing:
        agree = cmds.layoutDialog(ui=eula_prompt, title="Azure Batch Maya Client")
        if str(agree) != 'Agree':
            raise RuntimeError("Plugin initialization aborted.")
        cmds.optionVar(stringValue=(EULA_PREF, VERSION))
    else:
        agreed = cmds.optionVar(query=EULA_PREF)
        if StrictVersion(agreed) < VERSION:
            agree = cmds.layoutDialog(ui=eula_prompt, title="Azure Batch Maya Client")
            if str(agree) != 'Agree':
                raise RuntimeError("Plugin initialization aborted.")
            cmds.optionVar(stringValue=(EULA_PREF, VERSION))

    print("Checking for dependencies...")
    missing_libs = []
    for package in REQUIREMENTS:
        if not dependency_installed(package):
            missing_libs.append(package)
    for package in NAMESPACE_PACAKGES:
        if not dependency_installed(package):
            missing_libs.append(package)
    if missing_libs:
        message = ("One or more dependencies are missing or out-of-date."
                   "\nWould you like to install the following?\n\n")
        for lib in missing_libs:
            message += "{0} v{1}\n".format(*lib.split('=='))
        install = cmds.confirmDialog(
            title='Azure Batch', message=message, button=['Yes','No'],
            defaultButton='Yes', cancelButton='No', dismissString='No')

        if install == "No":
            cmds.confirmDialog(
                message="Could not load Azure Batch plug-in", button='OK')
            raise ImportError("Failed to load Azure Batch - "
                              "missing one or more dependencies")

        print("Attempting to install dependencies via Pip.")
        try:
            os.environ['PYTHONPATH'] = INSTALL_DIR + os.pathsep + os.environ['PYTHONPATH']
            install_script = os.path.normpath(os.path.join( os.environ['AZUREBATCH_TOOLS'], 'install_pip.py'))
            installer = subprocess.Popen(["mayapy", install_script, '--target', INSTALL_DIR])
            installer.wait()
            if installer.returncode != 0:
                raise RuntimeError("Failed to install pip")
        except BaseException as exp:
            print("Failed to install Pip. Please install dependencies manually to continue.")
            raise
        try:
            print("Installing dependencies")
            for package in missing_libs:
                install_pkg(package)
                if package in NAMESPACE_PACAKGES:
                    package_path = package.split('==')[0].split('-')
                    install_namespace_pkg(package, os.path.join(*package_path))
        except:
            error = "Failed to install dependencies - please install manually"
            cmds.confirmDialog(message=error, button='OK')
            raise ImportError(error)
        message = ("One or more dependencies have been successfully installed."
                   "\n Please restart Maya to complete installation.")
        cmds.confirmDialog(message=message, button='OK')
        raise ImportError("Please restart Maya. Azure Batch installed "
                          "Python dependencies.")

    print("Dependency check complete")
    plugin = OpenMayaMPx.MFnPlugin(
        obj, "Microsoft Corporation", VERSION, "Any")
    plugin.registerCommand(cmd_name, cmd_creator)

    try:
        if (mel.eval("""shelfLayout -exists "AzureBatch" """) == 0):
            mel.eval('addNewShelfTab %s' % "AzureBatch")
            mel.eval("""source "create_shelf.mel" """)
        melPath = get_usershelf_dir()
        if os.path.exists("{0}.deleted".format(melPath)):
            os.remove("{0}.deleted".format(melPath))
        os.rename(melPath, "{0}.deleted".format(melPath))
    except Exception as exp:
        print("Couldn't add shelf: {}".format(exp))

    # Add callback to clean up UI when Maya exits
    global fMayaExitingCB
    fMayaExitingCB = OpenMaya.MSceneMessage.addCallback(
        OpenMaya.MSceneMessage.kMayaExiting, remove_ui)


def uninitializePlugin(obj):
    """Remove and uninstall plugin."""
    print("Removing Azure Batch plug-in")
    plugin = MFnPlugin(obj)
    plugin.deregisterCommand(cmd_name)
    try:
        mel.eval('deleteShelfTab %s' % "AzureBatch")
    except:
        print("Couldn't delete shelf")
    global fMayaExitingCB
    if (fMayaExitingCB is not None):
        OpenMaya.MSceneMessage.removeCallback(fMayaExitingCB)
    if cmds.window("AzureBatch", exists=1):
        cmds.deleteUI("AzureBatch")
    AzureBatchSetup.remove_environment()
    print("Finished clearing up all Azure Batch components")


"""Check for environment and set up if not found."""
try:
    sys.path.extend(os.environ["AZUREBATCH_SCRIPTS"].split(os.pathsep))
    sys.path.append(os.environ['AZUREBATCH_MODULES'])
except KeyError as e:
    print("Couldn't find Azure Batch environment, setting up now...")
    setup_module()
