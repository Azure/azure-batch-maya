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
import logging
import json

from api import MayaAPI as maya
from api import MayaCallbacks as callback

from ui_environment import EnvironmentUI


MAYA_IMAGES = {
    'Batch Windows Preview':
        {
            'node_sku_id': 'batch.node.windows amd64',
            'publisher': 'batch',
            'offer': 'autodesk-maya-arnold-win2016-preview',
            'sku': 'maya2017',
            'version': 'latest'
        },
    'Batch CentOS Preview':
        {
            'node_sku_id': 'batch.node.centos 7',
            'publisher': 'batch',
            'offer': 'autodesk-maya-arnold-centos73-preview',
            'sku': 'maya2017',
            'version': 'latest'
        },
}
LICENSES = [
    {'label': 'Maya', 'id': 'maya', 'plugin': None },
    {'label': 'Arnold', 'id': 'arnold', 'plugin': 'mtoa' }
]
#

class AzureBatchEnvironment(object):
    """Handler for rendering environment configuration functionality."""
    
    def __init__(self, frame, call):
        """Create new Environment Handler.

        :param frame: The shared plug-in UI frame.
        :type frame: :class:`.AzureBatchUI`
        :param func call: The shared REST API call wrapper.
        """
        self._log = logging.getLogger('AzureBatchMaya')
        self._call = call
        self._session = None

        self.licenses = {}
        self._get_plugin_licenses()
        self.skus = self._load_skus()
        self.ui = EnvironmentUI(self, frame, MAYA_IMAGES.keys(), self.skus, self.licenses)
        self.refresh()
        #callback.after_new(self.ui.refresh)
        #callback.after_read(self.ui.refresh)

    def _load_skus(self):
        """Populate the list of availablke hardware SKUs."""
        sku_path = os.path.join(os.environ['AZUREBATCH_TOOLS'], 'skus.json')
        with open(sku_path, 'r') as sku_list:
            return json.load(sku_list)

    def _get_plugin_licenses(self):
        """Check whether the available license servers are required by the current
        scene in order to pre-select those that may be needed.
        """
        used_plugins = maya.plugins(query=True, pluginsInUse=True)
        used_plugins = used_plugins if used_plugins else []
        for license in LICENSES:
            if not license['plugin']:
                self.licenses[license['label']] = True
            elif license['plugin'] in used_plugins:
                self.licenses[license['label']] = True
            else:
                self.licenses[license['label']] = False

    def configure(self, session):
        """Populate the current session of the environment tab.
        Called on successful authentication.
        """
        self._session = session
        self.ui.select_image(self._session.get_cached_image())
        self.ui.select_sku(self._session.get_cached_vm_sku())

    def refresh(self):
        self._get_plugin_licenses()
        if self._session:
            self.ui.select_image(self._session.get_cached_image())
            self.ui.select_sku(self._session.get_cached_vm_sku())

    def get_application_licenses(self):
        license_servers = []
        for name, selected in self.licenses.items():
            if selected:
                license_servers.extend([v['id'] for v in LICENSES if v['label'] == name])
        return license_servers


    def set_image(self, image):
        self._session.store_image(image)

    def set_sku(self, sku):
        self._session.store_vm_sku(sku)

    def get_image(self):
        selected_image = self.ui.get_image()
        return dict(MAYA_IMAGES[selected_image])

    def get_vm_sku(self):
        return self.ui.get_sku()

    def os_flavor(self, pool_image=None):
        if pool_image:
            windows_offers = [value['offer'] for value in MAYA_IMAGES.values() if 'windows' in value['node_sku_id']]
            linux_offers = [value['offer'] for value in MAYA_IMAGES.values() if value['offer'] not in windows_offers]
            if pool_image.offer in windows_offers:
                return 'Windows'
            elif pool_image.offer in linux_offers:
                return 'Linux'
            else:
                raise ValueError('Selected pool is not using a valid Maya image.')

        if 'Windows' in self.ui.get_image():
            return 'Windows'
        else:
            return 'Linux'
