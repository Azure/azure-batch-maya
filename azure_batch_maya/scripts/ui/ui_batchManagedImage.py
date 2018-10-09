# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# -------------------------------------------------------------------------------------------- 

import azurebatchutils as utils

from enum import Enum
from azurebatchmayaapi import MayaAPI as maya

class BatchManagedImage(object):

    def __init__(self, parent, image_config):
        