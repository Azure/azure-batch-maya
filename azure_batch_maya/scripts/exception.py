# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import traceback
import logging

from azurebatchmayaapi import MayaAPI as maya

LOG = logging.getLogger('AzureBatchMaya')


class BatchMayaException(Exception):

    def __init__(self, *args):
        super(BatchMayaException, self).__init__(*args)


class CancellationException(BatchMayaException):

    def __init__(self, message, *args):
        super(CancellationException, self).__init__(message, *args)


class FileUploadException(BatchMayaException):

    def __init__(self, *args):
        super(FileUploadException, self).__init__(*args)


class PoolException(BatchMayaException):

    def __init__(self, *args):
        super(PoolException, self).__init__(*args)
