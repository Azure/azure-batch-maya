# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from .package_reference_base import PackageReferenceBase


class YumPackageReference(PackageReferenceBase):
    """A reference to a package to be installed using the YUM package
    manager on a Linux node.

    :param str id: The name of the package.
    :param str version: The version of the package to be installed. If omitted,
     the latest version (according to the package repository) will be installed.
    :param bool disable_excludes: Whether to allow packages that might otherwise
     be excluded by VM configuration (e.g. kernel packages). Default is False.
    """

    _validation = {
        'type': {'required': True},
        'id': {'required': True},
    }

    _attribute_map = {
        'type': {'key': 'type', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'version': {'key': 'version', 'type': 'str'},
        'disable_excludes': {'key': 'disableExcludes', 'type': 'bool'}
    }

    def __init__(self, id, version=None, disable_excludes=None):
        super(YumPackageReference, self).__init__(id=id, version=version)
        self.disable_excludes = disable_excludes
        self.type = 'yumPackage'
