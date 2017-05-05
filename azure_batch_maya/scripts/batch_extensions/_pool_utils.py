# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum

# pylint: disable=too-few-public-methods


class PoolOperatingSystemFlavor(Enum):
    WINDOWS = 'windows'
    LINUX = 'linux'


def get_pool_target_os_type(pool):
    try:
        image_publisher = pool.virtual_machine_configuration.image_reference.publisher
        sku_id = pool.virtual_machine_configuration.node_agent_sku_id
    except AttributeError:
        image_publisher = None
        sku_id = None

    return PoolOperatingSystemFlavor.WINDOWS \
        if not image_publisher \
        or (image_publisher and image_publisher.lower().find('windows') >= 0) \
        or (sku_id and sku_id.lower().find('windows') >= 0) \
        else PoolOperatingSystemFlavor.LINUX
