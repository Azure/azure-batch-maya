# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from msrest.serialization import Model


class PackageReferenceBase(Model):
    """A reference to a package to be installed on the compute nodes using 
    a package manager.

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

    _subtype_map = {
        'type': {'aptPackage': 'AptPackageReference',
                 'chocolateyPackage': 'ChocolateyPackageReference',
                 'yumPackage': 'YumPackageReference'}
    }

    def __init__(self, id, version=None):
        self.type = None
        self.id = id
        self.version = version
