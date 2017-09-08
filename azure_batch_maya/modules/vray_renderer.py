# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from maya import mel, cmds
import maya.OpenMaya as om
import maya.OpenMayaMPx as omp

import os
import sys
import gzip
import glob
import tempfile

from default import AzureBatchRenderJob, AzureBatchRenderAssets


class VrayRenderJob(AzureBatchRenderJob):

    render_engine = "vray"

    def __init__(self):

        self._renderer = "vray"
        self.label = "V-Ray"

    def settings(self):
        if self.scene_name == '':
            job_name = "Untitled"
        else:
            job_name = str(os.path.splitext(os.path.basename(self.scene_name))[0])
        file_prefix = cmds.getAttr("defaultRenderGlobals.imageFilePrefix")
        if file_prefix:
            file_prefix = os.path.split(file_prefix)[1]
        else:
            file_prefix = "<Scene>"

        self.job_name = self.display_string("Job Name:   ", job_name)
        self.output_name = self.display_string("Output Prefix:   ", file_prefix)

        self.start = self.display_int("Start frame:   ", self.start_frame, edit=True)
        self.end = self.display_int("End frame:   ", self.end_frame, edit=True)
        self.step = self.display_int("Frame step:   ", self.frame_step, edit=True)

    def get_title(self):
        return str(cmds.textField(self.job_name, query=True, text=True))

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
        return params


class VrayRenderAssets(AzureBatchRenderAssets):

    assets = []
    render_engine = "vray"
    file_nodes = {
        "VRayScannedMtl": ["file"],
        "VRayFastSSS2": ["prepassFileName"],
        "VRayMeshMaterial": ["fileName", "overrideFileName"],
        "VRayMtlGLSL": ["fileName"],
        "VRayMtlOSL": ["fileName"],
        "VRaySimbiont": ["file"],
        "VRayVRmatMtl": ["fileName"],
        "vraySettings": ["pmap_file",
                         "pmap_file2",
                         "causticsFile",
                         "causticsFile2",
                         "imap_fileName",
                         "imap_fileName2",
                         "lc_fileName",
                         "opt_fileName",
                         "shr_file_name"]
    }

    def check_path(self, path):
        if '#' in path:
            return path.replace('#', '[0-9]')
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
                    collected.append(cmds.getAttr(node + "." + attr))

        for path in collected:
            self.assets.append(self.check_path(path))
        return self.assets
