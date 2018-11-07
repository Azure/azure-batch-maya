# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import sys
import traceback
from collections import OrderedDict

from msrestazure.azure_cloud import AZURE_CHINA_CLOUD, AZURE_PUBLIC_CLOUD, AZURE_GERMAN_CLOUD, AZURE_US_GOV_CLOUD

AAD_ENVIRONMENTS = OrderedDict()
AAD_ENVIRONMENTS[AZURE_PUBLIC_CLOUD.name] = AZURE_PUBLIC_CLOUD
AAD_ENVIRONMENTS[AZURE_CHINA_CLOUD.name] = AZURE_CHINA_CLOUD
AAD_ENVIRONMENTS[AZURE_GERMAN_CLOUD.name] = AZURE_GERMAN_CLOUD 
AAD_ENVIRONMENTS[AZURE_US_GOV_CLOUD.name] = AZURE_US_GOV_CLOUD 

class AADEnvironmentProvider(object):

    def __init__(self, aad_environments = AAD_ENVIRONMENTS):
        self.aadEnvironments = aad_environments

    def  getAADEnvironments(self):
        return self.aadEnvironments

    def getEnvironmentForId(self, id):
        return AAD_ENVIRONMENTS[id]

    def getAadAuthorityHostUrl(self, id):
        return AAD_ENVIRONMENTS[id].endpoints.active_directory

    def getAadManagementUrl(self, id):
        return AAD_ENVIRONMENTS[id].endpoints.active_directory_resource_id

    def getBatchResourceUrl(self, id):
        return AAD_ENVIRONMENTS[id].endpoints.batch_resource_id

    def getResourceManager(self, id):
        return AAD_ENVIRONMENTS[id].endpoints.resource_manager
