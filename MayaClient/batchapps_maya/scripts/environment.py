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

import os
import logging

from api import MayaAPI as maya

from ui_environment import EnvironmentUI

IGNORE = ["Batchapps.py"]
SUPPORTED = ["Mayatomr.mll"]
DEFAULT = [
    "3dsImport.mll",
    "audioWave.mll",
    "closestPointOnCurve.mll",
    "corrosionTexture.mll",
    "cvColorShader.mll",
    "denimTexture.mll",
    "diffractionShader.mll",
    "drawReduceTool.mll",
    "drawSplitTool.mll",
    "frecklesTexture.mll",
    "gameInputDevice.mll",
    "hwColorPerVertexShader.mll",
    "hwManagedTextureShader.mll",
    "measure.mll",
    "nodeCreatedCBCmd.mll",
    "pointOnMeshInfo.mll",
    "polyNurbsProjection.mll",
    "PolyTools.mll",
    "polyVariance.mll",
    "randomizerDevice.mll",
    "ringsTexture.mll",
    "scallopTexture.mll",
    "skinShader.mll",
    "splatterTexture.mll",
    "streaksTexture.mll",
    "stringFormatNode.mll",
    "sun.mll",
    "treeBarkTexture.mll",
    "udpDevice.mll",
    "veiningTexture.mll",
    "woodGrainTexture.mll",
    "AbcExport.mll",
    "AbcImport.mll",
    "animImportExport.mll",
    "anzovinRigNodes.mll",
    "atomImportExport.mll",
    "AutodeskPacketFile.mll",
    "bullet.mll",
    "cgfxShader.mll",
    "cleanPerFaceAssignment.mll",
    "clearcoat.mll",
    "ddsFloatReader.mll",
    "dgProfiler.mll",
    "DirectConnect.mll",
    "fbxmaya.mll",
    "fltTranslator.mll",
    "Fur.mll",
    "ge2Export.mll",
    "gpuCache.mll",
    "hlslShader.mll",
    "hotOceanDeformer.mll",
    "ik2Bsolver.mll",
    "ikSpringSolver.mll",
    "matrixNodes.mll",
    "mayaCharacterization.mll",
    "mayaHIK.mll",
    "MayaMuscle.mll",
    "melProfiler.mll",
    "nearestPointOnMesh.mll",
    "objExport.mll",
    "OneClick.mll",
    "OpenEXRLoader.mll",
    "openInventor.mll",
    "quatNodes.mll",
    "retargeterNodes.py",
    "rotateHelper.mll",
    "rtgExport.mll",
    "stereoCamera.mll",
    "studioImport.mll",
    "Substance.mll",
    "TESTmaya.py",
    "tiffFloatReader.mll",
    "VectorRender.mll",
    "vrml2Export.mll"]

class BatchAppsEnvironment(object):
    
    def __init__(self, frame, call):

        self._log = logging.getLogger('BatchAppsMaya')
        self._call = call
        self._session = None

        self._maya_versions = ["Maya 2015", "MayaIO 2017"]
        self._plugins = self.get_plugins()

        self.ui = EnvironmentUI(self, frame)

    def configure(self, session):
        self._session = session

    def get_plugins(self):

        used_plugins = maya.plugins(query=True, pluginsInUse=True)
        extra_plugins = self.search_for_plugins()

        plugins = []

        for plugin in extra_plugins:
            enabled = maya.plugins(plugin, query=True, loaded=True)
            plugins.append([plugin, (plugin in SUPPORTED), enabled])


    def search_for_plugins(self):
        
        found_plugins = []
        search_locations = os.environ["MAYA_PLUG_IN_PATH"].split(os.pathsep)

        for plugin_dir in search_locations:
            if os.path.isdir(plugin_dir):
                plugins = os.listdir(os.path.normpath(plugin_dir))
                for plugin in plugins:
                    if (plugin.endswith(".mll") or plugin.endswith(".py")) and plugin not in IGNORE:
                        found_plugins.append(plugin)

        return list(set(found_plugins) - set(DEFAULT))
        