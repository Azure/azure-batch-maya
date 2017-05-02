# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from .package_reference_base import PackageReferenceBase


class ChocolateyPackageReference(PackageReferenceBase):
    """A reference to a package to be installed using the Chocolatey package
    manager on a Windows node.

    :param str id: The name of the package.
    :param str version: The version of the package to be installed. If omitted,
     the latest version (according to the package repository) will be installed.
    :param bool allow_empty_checksums: Whether Chocolatey will install packages
     without a checksum for validation. Default is false.
    """

    _validation = {
        'type': {'required': True},
        'id': {'required': True},
    }

    _attribute_map = {
        'type': {'key': 'type', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'version': {'key': 'version', 'type': 'str'},
        'allow_empty_checksums': {'key': 'allowEmptyChecksums', 'type': 'bool'}
    }

    def __init__(self, id, version=None, allow_empty_checksums=None):
        super(ChocolateyPackageReference, self).__init__(id=id, version=version)
        self.allow_empty_checksums = allow_empty_checksums
        self.type = 'chocolateyPackage'
