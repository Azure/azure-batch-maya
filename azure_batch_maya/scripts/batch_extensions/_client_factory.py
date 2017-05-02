# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.mgmt.batch import BatchManagementClient

import azure.batch.batch_service_client as batch
import azure.batch.batch_auth as batchauth

from azure.cli.core.commands.client_factory import get_mgmt_service_client


def account_mgmt_client_factory(kwargs):
    return batch_client_factory(**kwargs).batch_account


def batch_client_factory(**_):
    from azure.cli.command_modules.batch_extensions.version import VERSION
    client = get_mgmt_service_client(BatchManagementClient)
    client.config.add_user_agent('batch-extensions/v{}'.format(VERSION))
    return client


def batch_data_service_factory(kwargs):
    from azure.cli.command_modules.batch_extensions.version import VERSION
    account_name = kwargs['account_name']
    account_key = kwargs.pop('account_key', None)
    account_endpoint = kwargs['account_endpoint']

    credentials = None
    if not account_key:
        from azure.cli.core._profile import Profile, CLOUD
        profile = Profile()
        credentials, _, _ = profile.get_login_credentials(
            resource=CLOUD.endpoints.batch_resource_id)
    else:
        credentials = batchauth.SharedKeyCredentials(account_name, account_key)
    client = batch.BatchServiceClient(credentials, base_url=account_endpoint)
    client.config.add_user_agent('batch-extensions/v{}'.format(VERSION))
    return client
