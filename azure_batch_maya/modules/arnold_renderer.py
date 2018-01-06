# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import unicode_literals

import os
import sys
import gzip
import json
import re

from maya import mel, cmds
import maya.OpenMaya as om
import maya.OpenMayaMPx as omp

from default import AzureBatchRenderJob, AzureBatchRenderAssets

try:
    str_type = unicode
except NameError:
    str_type = str


class ArnoldRenderJob(AzureBatchRenderJob):

    render_engine = 'arnold'

    def __init__(self):
        self._renderer = 'arnold'
        self.label = 'Arnold'
        self.log_levels = [
            "0 - Errors",
            "1 - Warnings + Info",
            "2 - Debug"
        ]

    def settings(self):
        if self.scene_name == '':
            job_name = "Untitled"
        else:
            job_name = str_type(os.path.splitext(os.path.basename(self.scene_name))[0])
        file_prefix = cmds.getAttr("defaultRenderGlobals.imageFilePrefix")
        if file_prefix:
            file_prefix = os.path.split(file_prefix)[1]
        else:
            file_prefix = "<Scene>"
        self.job_name = self.display_string("Job name:   ", job_name)
        self.output_name = self.display_string("Output prefix:   ", file_prefix)
        self.start = self.display_int("Start frame:   ", self.start_frame, edit=True)
        self.end = self.display_int("End frame:   ", self.end_frame, edit=True)
        self.step = self.display_int("Frame step:   ", self.frame_step, edit=True)

        try:
            log_level = cmds.getAttr("defaultArnoldRenderOptions.log_verbosity")
        except ValueError:
            log_level = 1
        self.logging = self.display_menu("Logging:   ", self.log_levels, log_level+1)

    def get_title(self):
        return str_type(cmds.textField(self.job_name, query=True, text=True))

    def render_enabled(self):
        return True

    def get_jobdata(self):
        if self.scene_name == '':
            raise ValueError("Current Maya scene has not been saved to disk.")
        
        pending_changes = cmds.file(query=True, modified=True)
        if not pending_changes:
            return self.scene_name, [self.scene_name]
        options = {
            'save': "Save and continue",
            'nosave': "Continue without saving",
            'cancel': "Cancel"
        }
        answer = cmds.confirmDialog(title="Unsaved Changes",
                                    message="There are unsaved changes. Continue?",
                                    button=options.values(),
                                    defaultButton=options['save'],
                                    cancelButton=options['cancel'],
                                    dismissString=options['cancel'])
        if answer == options['cancel']:
            raise Exception("Submission cancelled")
        if answer == options['save']:
            cmds.SaveScene()
        return self.scene_name, [self.scene_name]

    def get_params(self):
        params = {}
        params['frameStart'] = cmds.intField(self.start, query=True, value=True)
        params['frameEnd'] = cmds.intField(self.end, query=True, value=True)
        params['frameStep'] = cmds.intField(self.step, query=True, value=True)
        params['renderer'] = self._renderer
        params['logLevel'] = int(cmds.optionMenu(self.logging, query=True, select=True)) - 1
        return params


class ArnoldRenderAssets(AzureBatchRenderAssets):

    assets = []
    render_engine = 'arnold'
    replace_pattern = re.compile(r'#+')
    file_nodes = {
        'aiStandIn': ['dso'],
        'aiPhotometricLight': ['aiFilename'],
        'aiVolume': ['filename'],
        'aiImage': ['filename']
    }

    def check_path(self, path):
        """
        TODO: The pattern replacements are currently not strict enough,
        for example:
            'test.#.png' will match test.1.png, test.1001.png, test.1test.png, test.9.9.test.png
            when we only want to match test.1.png and test.1001.png.
        We need to replace with a proper regex match as glob is insufficient.
        Other assumptions:
            - Asset patterns will ONLY occur in the filename, not the path.
            - A UDIM reference will always be 4 digits.
            - A single '#' character can represent multiple digits.
        """
        if '#' in path:
            return self.replace_pattern.sub('[0-9]*', path)
        elif '<udim>' in path:
            return path.replace('<udim>', '[0-9][0-9][0-9][0-9]')
        elif '<tile>' in path:
            return path.replace('<tile>', '_u*_v*')
        else:
            return path

    def renderer_assets(self):
        self.assets = []
        collected = []
        for node_type, attributes in self.file_nodes.items():
            nodes = cmds.ls(type=node_type)
            for node in nodes:
                for attr in attributes:
                    path = cmds.getAttr(node + '.' + attr)
                    if path:
                        collected.append(path)
        for path in collected:
            self.assets.append(self.check_path(path))
        return self.assets
    
    def setup_script(self, script_handle, pathmap, searchpaths):
        search_path = ';'.join(searchpaths).encode('utf-8')
        procedural_searchpath = str("setAttr -type \"string\" defaultArnoldRenderOptions.procedural_searchpath \"{}\";\n").format(search_path)
        plugin_searchpath = str("setAttr -type \"string\" defaultArnoldRenderOptions.plugin_searchpath \"{}\";\n").format(search_path)
        texture_searchpath = str("setAttr -type \"string\" defaultArnoldRenderOptions.texture_searchpath \"{}\";\n").format(search_path)
        script_handle.write(procedural_searchpath)
        script_handle.write(plugin_searchpath)
        script_handle.write(texture_searchpath)
        
        # This kind of explicit asset re-direct is kinda ugly - so far
        # it only seems to be needed on aiImage nodes, which appear to
        # be bypassed by the 'dirmap' command. We may need to extend this
        # to other ai node types.
        script_handle.write("$aiImageNodes = `ls -type aiImage`;\n")
        script_handle.write("for ( $aiImageNode in $aiImageNodes ) {\n")
        script_handle.write("string $fullname = `getAttr ($aiImageNode + \".filename\")`;\n")
        script_handle.write("string $basename = basename($fullname, \"\");\n")
        script_handle.write("setAttr  -type \"string\" ($aiImageNode + \".filename\") $basename;\n")
        script_handle.write("}\n")
