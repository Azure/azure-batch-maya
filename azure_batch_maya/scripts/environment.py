# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import unicode_literals

import os
import logging
import json

from azure.batch_extensions import models

from azurebatchmayaapi import MayaAPI as maya
from azurebatchmayaapi import MayaCallbacks as callback
import azurebatchutils as utils
from ui_environment import EnvironmentUI
from ui_environment import PoolImageMode
from poolImageProvider import MARKETPLACE_IMAGES

from collections import OrderedDict

LICENSES = [
    {'label': 'Maya', 'id': 'maya', 'plugin': None },
    {'label': 'Arnold', 'id': 'arnold', 'plugin': 'mtoa' },
    {'label': 'V-Ray', 'id': 'vray', 'plugin': 'vrayformaya' }
]


class AzureBatchEnvironment(object):
    """Handler for rendering environment configuration functionality."""
    
    def __init__(self, index, frame, call):
        """Create new Environment Handler.

        :param index: The UI tab index.
        :param frame: The shared plug-in UI frame.
        :type frame: :class:`.AzureBatchUI`
        :param func call: The shared REST API call wrapper.
        """
        self._log = logging.getLogger('AzureBatchMaya')
        self._call = call
        self._session = None
        self._submission = None
        self._tab_index = index
        self.node_agent_sku_id_list = None

        self.licenses = OrderedDict()
        self._get_plugin_licenses()
        self.skus = self._load_skus()
        self.ui = EnvironmentUI(self, frame, MARKETPLACE_IMAGES.keys(), self.skus, self.licenses)
        self.refresh()

    def _load_skus(self):
        """Populate the list of available hardware SKUs."""
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

    def configure(self, session, submission):
        """Populate the current session of the environment tab.
        Called on successful authentication.
        """
        self._session = session
        self._submission = submission
        self.batch = self._session.batch
        self.ui.select_image(self._session.batch_image)
        self.ui.select_sku(self._session.vm_sku)
        
    def refresh(self):
        self._get_plugin_licenses()
        if self._session:
            self.ui.select_image(self._session.batch_image)
            self.ui.select_sku(self._session.vm_sku)

    def get_application_licenses(self):
        license_servers = []
        for name, selected in self.licenses.items():
            if selected:
                license_servers.extend([v['id'] for v in LICENSES if v['label'] == name])
        return license_servers

    def get_image_type(self):
        return self.ui.get_image_type()

    def build_container_configuration(self):
        if self.ui.get_image_type().value == PoolImageMode.CONTAINER_IMAGE.value:
            container_configuration = models.ContainerConfiguration(container_image_names=self.ui.get_pool_container_images())
            return container_configuration
        return None

    def get_pool_container_images(self):
        return self.ui.get_pool_container_images()

    def get_task_container_image(self):
        return self.ui.get_task_container_image()

    def build_virtualmachineconfiguration(self):
        image_reference = self.get_image_reference()
        vm_config = models.VirtualMachineConfiguration(
            image_reference=image_reference,
            node_agent_sku_id=self.get_node_sku_id(),
            container_configuration = self.build_container_configuration())
        
        return vm_config

    def set_node_sku_id(self, node_sku_id):
        self._session.node_sku_id = node_sku_id

    def retrieve_node_agent_skus(self):
        node_agent_sku_list =  self._call(self.batch.account.list_node_agent_skus)
        self.node_agent_sku_id_list = [nodeagentsku.id for nodeagentsku in node_agent_sku_list]

    def node_agent_skus(self):
        if not self.node_agent_sku_id_list:
            self.retrieve_node_agent_skus()
        return self.node_agent_sku_id_list 
    
    def get_image_reference(self):
        if self.get_image_type().value == PoolImageMode.MARKETPLACE_IMAGE.value:
            image = self.get_marketplace_image()
            image.pop('node_sku_id')
            image_reference = models.ImageReference(**image)
            return image_reference
        if self.get_image_type().value == PoolImageMode.CONTAINER_IMAGE.value:
            image = self.ui.get_container_image_reference()
            image_reference = models.ImageReference(**image)
            return image_reference

    def get_node_sku_id(self):
        return self.ui.get_node_sku_id()

    def get_marketplace_image(self):
        selected_image = self.ui.get_selected_marketplace_image()
        return dict(MARKETPLACE_IMAGES[selected_image])

    def get_image_label(self, image_ref):
        """Retrieve the image label from the data in a pool image
        reference object.
        """
        pool_image = [k for k,v in MARKETPLACE_IMAGES.items() if v['offer'] == image_ref.offer]
        if pool_image:
            return pool_image[0]
        else:
            self._log.debug("Pool using unknown image reference: {}".format(image_ref.offer))
            return image_ref.offer

    def os_flavor(self, pool_image=None):
        node_sku_id = self.get_node_sku_id()
        if 'windows' in node_sku_id:
            self._log.debug("Detected windows for skuId: {}".format(node_sku_id))
            return utils.OperatingSystem.windows
        else:
            self._log.debug("Detected Linux for skuId: {}".format(node_sku_id))
            return utils.OperatingSystem.linux

    def get_environment_settings(self):
        env_vars = self.ui.get_env_vars()
        vars = [{'name': k, 'value': v} for k, v in env_vars.items()]
        self._log.debug("Adding custom env vars: {}".format(vars))
        return vars

    @property
    def batch_image(self):
        return self._session.batch_image
    @batch_image.setter
    def batch_image(self, value):
        self._session.batch_image = value

    @property
    def node_sku_id(self):
        return  self._session.node_sku_id
    @node_sku_id.setter
    def node_sku_id(self, value):
       self._session.node_sku_id = value

    @property
    def vm_sku(self):
        return self._session.vm_sku
    @vm_sku.setter
    def vm_sku(self, value):
       self._session.vm_sku = value
