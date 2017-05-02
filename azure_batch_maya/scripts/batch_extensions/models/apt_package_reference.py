# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from .package_reference_base import PackageReferenceBase


class AptPackageReference(PackageReferenceBase):
    """A reference to a package to be installed using the APT package
    manager on a Linux node (apt-get).

    :param str id: The name of the package.
    :param str version: The version of the package to be installed. If omitted,
     the latest version (according to the package repository) will be installed.
    """

    _validation = {
        'type': {'required': True},
        'id': {'required': True},
    }

    _attribute_map = {
        'type': {'key': 'type', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'version': {'key': 'version', 'type': 'str'},
    }

    def __init__(self, id, version=None):
        super(AptPackageReference, self).__init__(id=id, version=version)
        self.type = 'aptPackage'
