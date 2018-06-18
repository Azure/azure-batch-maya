# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import unicode_literals

import os
import logging
import json

from azure.batch import models

from azurebatchmayaapi import MayaAPI as maya
from azurebatchmayaapi import MayaCallbacks as callback
import azurebatchutils as utils
from ui_environment import EnvironmentUI
from ui_environment import ImageType

MAYA_IMAGES = {
    'Windows 2016':
        {
            'node_sku_id': 'batch.node.windows amd64',
            'publisher': 'batch',
            'offer': 'rendering-windows2016',
            'sku': 'rendering',
            'version': '1.2.1'
        },
    'Centos 73':
        {
            'node_sku_id': 'batch.node.centos 7',
            'publisher': 'batch',
            'offer': 'rendering-centos73',
            'sku': 'rendering',
            'version': '1.1.2'
        },
}
LICENSES = [
    {'label': 'Maya', 'id': 'maya', 'plugin': None },
    {'label': 'Arnold', 'id': 'arnold', 'plugin': 'mtoa' },
    {'label': 'V-Ray', 'id': 'vray', 'plugin': 'vrayformaya' }
]
#

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
        self._tab_index = index
        self.node_agent_sku_id_list = None

        self.licenses = {}
        self._get_plugin_licenses()
        self.skus = self._load_skus()
        self.ui = EnvironmentUI(self, frame, MAYA_IMAGES.keys(), self.skus, self.licenses)
        self.refresh()
        #callback.after_new(self.ui.refresh)
        #callback.after_read(self.ui.refresh)

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

    def configure(self, session):
        """Populate the current session of the environment tab.
        Called on successful authentication.
        """
        self._session = session
        self.batch = self._session.batch
        self.ui.select_node_sku_id(self._session.get_cached_node_sku_id())
        self.ui.select_custom_image_resource_id(self._session.get_cached_custom_image_resource_id())
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

    def get_image_type(self):
        return self.ui.get_image_type()

    def build_container_configuration(self):
        return models.containerConfiguration(
            container_registries=self.get_container_registries(),
            container_image_names=self.get_container_images())

    def build_virtualmachineconfiguration(self):
        vm_config = models.VirtualMachineConfiguration(
            image_reference=self.get_image_reference(),
            node_agent_sku_id=self.get_node_sku_id())

        if self.ui.get_image_type == ImageType.CUSTOM_IMAGE_WITH_CONTAINERS:
            vm_config.container_configuration = models.ContainerConfiguration(
                container_registries=self.get_container_registries(),
                container_image_names=self.get_container_images())
        return vm_config

    def get_container_registries(self):
        containerRegistries = []
        containerRegistries.append(models.ContainerRegistry(
            user_name=self.ui.get_container_registry_username(),
            password = self.ui.get_container_registry_password(),
            registry_server = self.ui.get_container_registry_server()))
        return containerRegistries

    def get_container_images(self):
        containerImages = []
        containerImages.append(self.ui.get_container_image())
        return containerImages

    def set_sku(self, sku):
        self._session.store_vm_sku(sku)

    def set_node_sku_id(self, node_sku_id):
        self._session.store_node_sku_id(node_sku_id)

    def retrieve_node_agent_skus(self):
        node_agent_sku_list =  self._call(self.batch.account.list_node_agent_skus)
        self.node_agent_sku_id_list = [nodeagentsku.id for nodeagentsku in node_agent_sku_list]

    def node_agent_skus(self):
        if not self.node_agent_sku_id_list:
            self.retrieve_node_agent_skus()
        return self.node_agent_sku_id_list 
    
    def get_image_reference(self):
        if self.get_image_type == ImageType.BATCH_IMAGE:
            image = self.get_batch_image()
            image.pop('node_sku_id')
            return models.ImageReference(**image)
        return models.ImageReference(virtual_machine_image_id=self.ui.get_custom_image_resource_id())

    def get_node_sku_id(self):
        if self.get_image_type == ImageType.BATCH_IMAGE:
            image = self.get_batch_image()
            return image.pop('node_sku_id')
        return self.ui.get_node_sku_id()

    def get_batch_image(self):
        selected_image = self.ui.get_os_image()
        return dict(MAYA_IMAGES[selected_image])

    def get_custom_image_resource_id(self):
        selected_image = self.ui.get_os_image()
        return dict(MAYA_IMAGES[selected_image])

    def set_custom_image_resource_id(self, custom_image_resource_id):
        self._session.store_custom_image_resource_id(custom_image_resource_id)

    def get_image_label(self, image_ref):
        """Retrieve the image label from the data in a pool image
        reference object.
        """
        pool_image = [k for k,v in MAYA_IMAGES.items() if v['offer'] == image_ref.offer]
        if pool_image:
            return pool_image[0]
        else:
            self._log.debug("Pool using unknown image reference: {}".format(image_ref.offer))
            return image_ref.offer

    def get_vm_sku(self):
        return self.ui.get_sku()

    def os_flavor(self, pool_image=None):
        if pool_image:
            windows_offers = [value['offer'] for value in MAYA_IMAGES.values() if 'windows' in value['node_sku_id']]
            linux_offers = [value['offer'] for value in MAYA_IMAGES.values() if value['offer'] not in windows_offers]
            if pool_image.offer in windows_offers:
                return utils.OperatingSystem.windows
            elif pool_image.offer in linux_offers:
                return utils.OperatingSystem.linux
        node_sku_id = self.ui.get_node_sku_id()
        if utils.OperatingSystem.windows.value.lower() in node_sku_id:
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
