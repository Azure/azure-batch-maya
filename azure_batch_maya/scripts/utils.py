# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum
import os
import logging
import platform
import pathlib

from api import MayaAPI as maya

from batch_extensions import _file_utils as file_utils
from exception import CancellationException, FileUploadException


MAX_LOCAL_PATH_LENGTH = 150


def shorten_path(path, filename):
    """Iteratively remove directories from the end of a file path
    until it meets the Windows max path length requirements when
    if is downloaded to the render node.
    """
    while len(os.path.join(path, filename)) > MAX_LOCAL_PATH_LENGTH:
        path = os.path.dirname(path)
    return path


def get_storage_file_path(fullpath):
    """Generate the virtual directory path of the asset in
    Azure storage.
    """
    path = shorten_path(*os.path.split(fullpath))
    if ':' in path:
        drive_letter, path = path.split(':', 1)
        path = drive_letter + '/' + path[1:]
    return path.replace('\\', '/')


def get_remote_file_path(assetpath):
    """Generate remote asset path. Returns a function
    to allow for delayed generation based on the selected
    pool os flavor at job submission time.
    """
    def generate_path(os_flavor, fullpath=assetpath):
        local_sep = os.sep
        remote_sep = '\\' if os_flavor == OperatingSystem.windows else '/'
        path = shorten_path(*os.path.split(fullpath))
        if ':' in path:
            drive_letter, path = path.split(':', 1)
            path = drive_letter + local_sep + path[1:]
        path = path.replace('/', remote_sep).replace('\\', remote_sep)
        return path.strip('\\/').replace('\\', '\\\\')
    return generate_path


def get_remote_directory(dir_path, os_flavor):
    """Convert a local directory path to a remote directory
    path according to the remote OS.
    """
    local_sep = os.sep
    remote_sep = '\\' if os_flavor == OperatingSystem.windows else '/'
    if ':' in dir_path:
        drive_letter, dir_path = dir_path.split(':', 1)
        dir_path = drive_letter + local_sep + dir_path[1:]
    dir_path = dir_path.replace('/', remote_sep).replace('\\', remote_sep)
    return dir_path.strip('\\/').replace('\\', '\\\\')


def format_scene_path(scene_file, os_flavor):
    """Format the Maya scene file path according to where it will
    be on the render node.
    """
    scene_path = get_remote_file_path(scene_file)(os_flavor)
    if os_flavor == OperatingSystem.windows:
        return "X:\\\\" + scene_path + '\\\\' + os.path.basename(scene_file)
    else:
        return "/X/" + scene_path + '/' + os.path.basename(scene_file)


def get_default_output_path():
    """Get the render output directory as specified in the current
    Maya project.

    :returns: The output directory (str).
    """
    path = maya.workspace(fileRuleEntry="images")
    output_path = maya.workspace(en=path)
    return output_path


def get_os():
    """Get the current operating system.
    :returns: The OS platform (str).
    """
    return platform.system()


class OperatingSystem(Enum):
    windows = 'Windows'
    linux = 'Linux'
    darwin = 'Darwin'


class Row(object):
    """UI row class."""

    def __init__(self, columns, adjust, width, align=None, row=None, parent=None):
        kwargs = {}
        kwargs["numberOfColumns"] = int(columns)
        kwargs["columnWidth{0}".format(columns)] = width
        kwargs["adjustableColumn"] = adjust
        kwargs["columnAttach{0}".format(columns)] = columns*["both"] if columns>1 else "both"
        kwargs["columnOffset{0}".format(columns)] = columns*[5] if columns>1 else 5
        if row:
            kwargs["rowAttach"] = row
        if align:
            kwargs["columnAlign{0}".format(columns)] = align
        if parent:
            kwargs["parent"] = parent
        self._row = maya.row(**kwargs)

    def __enter__(self):
        return self._row

    def __exit__(self, type, value, traceback):
        maya.parent()

class Layout(object):
    """Parent layout class."""

    def __init__(self, form, **kwargs):
        """Create a new layout based on the supplied layout form and args.

        :param form: The layout object to be created.
        :type form: :class:`maya.cmds.Layout`
        :param kwargs: Any properties to apply to the layout.
        """
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
        if kwargs.get("row_attach"):
            settings["rowAttach"] = kwargs["row_attach"]
        if kwargs.get("adjust"):
            settings["adjustableColumn"] = kwargs["adjust"]
        if kwargs.get("layout"):
            settings.update(kwargs["layout"])
        self.layout = self.form(**settings)

    def __enter__(self):
        return self.layout

    def __exit__(self, type, value, traceback):
        maya.parent()


class RowLayout(Layout):
    """Wrapper class for :class:`maya.cmds.rowLayout`."""

    def __init__(self, **kwargs):
        kwargs["adjust"] = True
        super(RowLayout, self).__init__(maya.row_layout, **kwargs)


class FrameLayout(Layout):
    """Wrapper class for :class:`maya.cmds.frameLayout`."""

    def __init__(self, **kwargs):
        settings = {}
        if kwargs.get("label"):
            settings["label"] = kwargs["label"]
        if kwargs.get("collapsable"):
            settings["collapsable"] = kwargs["collapsable"]
        super(FrameLayout, self).__init__(
            maya.frame_layout, layout=settings, **kwargs)

class GridLayout(Layout):
    """Wrapper class for :class:`maya.cmds.gridLayout`."""

    def __init__(self, **kwargs):
        settings = {}
        if kwargs.get("rows"):
            settings["numberOfRows"] = kwargs["rows"]
        if kwargs.get("cols"):
            settings["numberOfColumns"] = kwargs["cols"]
        if kwargs.get("width"):
            settings["cellWidth"] = kwargs["width"]
        super(GridLayout, self).__init__(
            maya.grid_layout, layout=settings, **kwargs)


class ColumnLayout(Layout):
    """Wrapper class for :class:`maya.cmds.columnLayout`."""

    def __init__(self, columns, **kwargs):
        settings = {"numberOfColumns": columns}
        if kwargs.get("col_width"):
            settings["columnWidth"] = kwargs["col_width"]
        if kwargs.get("row_offset"):
            settings["rowOffset"] = kwargs["row_offset"]
        if kwargs.get("row_height"):
            settings["rowHeight"] = kwargs["row_height"]
        if kwargs.get("col_align"):
            settings["columnAlign"] = kwargs["col_align"]
        super(ColumnLayout, self).__init__(
            maya.col_layout, layout=settings, **kwargs)


class ScrollLayout(Layout):
    """Wrapper class for :class:`maya.cmds.scrollLayout`."""

    def __init__(self, **kwargs):
        settings = {"horizontalScrollBarThickness": 0,
                    "verticalScrollBarThickness": 3,
                    "childResizable":True}
        super(ScrollLayout, self).__init__(
            maya.scroll_layout, layout=settings, **kwargs)


class ClickMenu(object):
    """Wrapper class for :class:`maya.cmds.popupMenu`."""

    def __init__(self, command, **kwargs):
        """Create new right-click menu.

        :param func command: The function to call when a menu item
         is selected.
        """
        self.menu = maya.popup_menu(**kwargs)
        self.command = command

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def add_item(self, item):
        """Add menu item. Item will be passed into self.command.
        :param str item: The item to add.
        """
        maya.menu_option(
            label=item, parent=self.menu, command=lambda a: self.command(item))

class Dropdown(object):
    """Wrapper class for :class:`maya.cmds.menu`."""

    def __init__(self, command, **kwargs):
        """Create new dropdown menu.
        :param func command: Function to be called when a menu item
         is selected.
        """

        self.menu = maya.menu(changeCommand=command, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass
        #maya.parent()

    def add_item(self, item):
        """Add item to the menu
        :param str item: Menu option to add.
        """
        maya.menu_option(label=item, parent=self.menu)

    def selected(self):
        """Get selected option.
        :returns: The index (int) of the selected option.
        """
        return int(maya.menu(self.menu, query=True, select=True))

    def value(self):
        """Get the selected option.
        :returns: The value (str) of the selected option.
        """
        return str(maya.menu(self.menu, query=True, value=True))

    def select(self, value):
        """Select a specific option in the menu.
        :param int value: The index of the option to select.
        """
        try:
            maya.menu(self.menu, edit=True, select=int(value))
        except ValueError:
            maya.menu(self.menu, edit=True, value=value)


class ProgressBar(object):
    """Wrapper class for :class:`maya.cmds.mainProgressBar`."""

    def __init__(self, log):
        """Create and start new progress bar."""
        self.done = False
        self._log = log
        self._progress = maya.mel('$tmp = $gMainProgressBar')
        maya.progress_bar(self._progress, edit=True,
                          beginProgress=True, isInterruptable=True)

    def end(self):
        """End the progress bar."""
        maya.progress_bar(self._progress, edit=True, endProgress=True)

    def is_cancelled(self):
        """Check whether process has been cancelled.
        :returns: True if cancelled else False.
        """
        if maya.progress_bar(self._progress, query=True, isCancelled=True):
            self.done = True
            self.end()
            raise CancellationException("File upload cancelled")
        self._log.debug("not cancelled")

    def step(self):
        """Step progress bar forward by one."""
        maya.progress_bar(self._progress, edit=True, step=1)

    def status(self, status):
        """Update status label of progress bar.
        :param str status: The updated status label.
        """
        self._log.debug("Progress status: {}".format(status))
        maya.progress_bar(self._progress, edit=True, status=str(status))

    def max(self, max_value):
        """Set the max number of steps in the progress bar.
        :param int max_value: Number of intervals.
        """
        maya.progress_bar(self._progress, edit=True, maxValue=int(max_value))


class HoldButton(object):

    def __init__(self, *args, **kwargs):
        self._button = maya.button(*args, **kwargs)

    @property
    def display(self):
        """Returns the :class:`maya.cmds.button` object."""
        return self._button

    def hold(self):
        """Place the button in a processing state."""
        maya.button(self._button, edit=True, enable=False)
        maya.refresh()

    def release(self):
        """Finish the buttons processing state."""
        maya.button(self._button, edit=True, enable=True)
        maya.refresh()


class ProcButton(object):
    """Wrapper class for :class:`maya.cmds.button` for long running
    processes.
    """

    def __init__(self, label, proc_label, command, *args, **kwargs):
        """Create new process button.

        :param str label: The label for the button.
        :param str proc_label: The label for the button while in a
         processing state.
        :param func command: The function the button executes.
        """
        self.label = label
        self.prob_label = proc_label
        self._button = maya.button(
            label=self.label, command=command, *args, **kwargs)

    @property
    def display(self):
        """Returns the :class:`maya.cmds.button` object."""
        return self._button

    def start(self):
        """Place the button in a processing state."""
        maya.button(
            self._button, edit=True, enable=False, label=self.prob_label)
        maya.refresh()

    def update(self, update):
        """Update the button label with process status.
        :param str update: The status to display on the label.
        """
        update = "{0} [Press ESC to cancel]".format(update)
        maya.button(self._button, edit=True, enable=False, label=update)
        maya.refresh()

    def enable(self, enabled):
        """Enable or disable the button.
        :param bool enabled: Whether to enable the button.
        """
        maya.button(self._button, edit=True, enable=enabled)
        maya.refresh()

    def finish(self):
        """Finish the buttons processing state."""
        maya.button(self._button, edit=True, enable=True, label=self.label)
        maya.refresh()


class JobWatcher(object):
    """Class for background job watcher."""

    def __init__(self, id, data_path, dir):
        """Create a new job watcher.

        :param str id: The ID of the job to watch.
        :param str data_path: The path of the AzureBatch config dir.
        :param str dir: The path of directory where outputs will be 
         downloaded.
        """
        self.job_id = id
        self.data_path = data_path
        self.selected_dir = dir
        self._log = logging.getLogger('AzureBatchMaya')
        self.job_watcher = os.path.join(
            os.path.dirname(__file__), "tools", "job_watcher.py")
        platform = get_os()
        if platform == OperatingSystem.windows.value:
            self.proc_cmd = 'system("WMIC PROCESS where (Name=\'mayapy.exe\') get Commandline")'
            self.start_cmd = 'system("start mayapy {0}")'
            self.quotes = '\\"'
            self.splitter = 'mayapy'
        elif platform == OperatingSystem.darwin.value:
            self.proc_cmd = 'system("ps -ef")'
            self.start_cmd = 'system("osascript -e \'tell application \\"Terminal\\" to do script \\"python {0}\\"\'")'
            self.quotes = '\\\\\\"'
            self.splitter = '\n'
        else:
            maya.warning("Cannot launch job watcher: OS not supported.")
            return
        self.start_job_watcher() 

    def start_job_watcher(self, *args):
        """Launch job watcher process using mayapy."""
        try:
            if not self.check_existing_process():
                args = self.prepare_args()
                command = self.start_cmd.format(" ".join(args))
                self._log.debug("Running command: {0}".format(command))
                maya.mel(command)
                self._log.info("Job watching for job with id {0}"
                               " has started.".format(args[2]))
            else:
                maya.warning("Existing process running with current job ID. "
                             "Job watching already in action.")
        except Exception as e:
            maya.warning(e)

    def check_existing_process(self):
        """Check whether a job watcher for the specified job is already running.
        :returns: True if a process already exists else False.
        """
        self._log.info("Checking that a job watching process is not "
                       "already running for this job.")
        processes = maya.mel(self.proc_cmd)
        processes = processes.split(self.splitter)
        running = [proc for proc in processes if proc.find(self.job_id) >= 0]
        if running:
            return True
        return False

    def prepare_args(self):
        """Prepare the command args to execute with mayapy.
        :returns: A list of clean args (str).
        """
        args = [self.job_watcher, 
                self.data_path,
                self.job_id,
                self.selected_dir,
                file_utils._get_container_name(self.job_id),
                os.path.join(maya.script_dir(), 'azure-batch-libs')]  # TODO: Configure somewhere
        self._log.debug("Preparing commandline arguments...")
        return self.cleanup_args(args)

    def cleanup_args(self, args):
        """Clean up path command line args to double back-slashes and quote
        strings for successful mel execution.

        :param list args: List of str args to be cleaned.
        :returns: List of cleaned string args.
        """
        prepared_args = []
        for arg in args:
            arg = os.path.normpath(arg).replace('\\', '\\\\')
            prepared_args.append(self.quotes + str(arg) + self.quotes)
        self._log.debug("Cleaned up commandline arguments: {0}, {1}, "
                        "{2}, {3}, {4}".format(*prepared_args))
        return prepared_args
