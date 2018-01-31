# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import unicode_literals

import webbrowser
import ConfigParser
import time
import sys
import os
import re
import threading
import json
import traceback
import datetime
import dateutil.tz
from dateutil.parser import parse as dateparse
from azure.batch.models import BatchErrorException

try:
    str = unicode
except NameError:
    pass
batch_client = None
storage_client = None
header_line_length = 50

batchAadResource = "https://batch.core.windows.net/"
mgmtAadResource = "https://management.core.windows.net/"
aadTenant = "microsoft.onmicrosoft.com"
aadAuthorityHostUrl = "https://login.microsoftonline.com"
aadClientId = "04b07795-8ddb-461a-bbee-02f9e1bf7b46" #Azure CLI


def header(header):
    header_chars = len(header)
    dashes = header_line_length - header_chars
    mult = int(dashes/2)
    padded = "\n\n" + mult*"-" + header + mult*"-"
    if dashes % 2 > 0:
        padded += "-"
    return padded


def _check_valid_dir(directory):
    try:
        log_dir = os.path.join(directory, "logs")
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        return directory

    except (TypeError, EnvironmentError) as exp:
        raise RuntimeError(exp)


def _download_output(job_id, output_name, output_path, size):
    print("Downloading task output: {}".format(output_name))
    batch_client.file.download(output_path, job_id, remote_path=output_name)
    print("Output {} download successful".format(output_name))


def _track_completed_outputs(job_id, dwnld_dir):
    job_outputs = batch_client.file.list_from_group(job_id)
    downloads = []
    for output in job_outputs:
        if output['name'].startswith('thumbs/'):
            continue
        else:
            downloads.append(
                threading.Thread(
                    target=_download_output,
                    args=(job_id, output['name'], dwnld_dir, output['size'])))
            downloads[-1].start()
            if len(downloads) >= batch_client.threads:
                for thread in downloads:
                    thread.join()
                downloads = []
    for thread in downloads:
        thread.join()


def _check_job_stopped(job):
    """Checks job for failure or completion.
    :returns: A boolean indicating True if the job completed, or False if still in
     progress.
    :raises: RuntimeError if the job has failed, or been cancelled.
    """
    from azure.batch.models import JobState
    stopped_status = [
        JobState.disabling,
        JobState.disabled,
        JobState.terminating,
        JobState.deleting
    ]
    running_status = [
        JobState.active,
        JobState.enabling
    ]
    try:
        if job.state in stopped_status:
            print(header("Job has stopped"))
            print("Job status: {0}".format(job.state))
            raise RuntimeError("Job is no longer active. State: {0}".format(job.state))
        elif job.state == JobState.completed:
            print(header("Job has completed"))
            return True
        elif job.state in running_status:
            return False
        else:
            raise RuntimeError("Job state invalid: {}".format(job.state))
    except AttributeError as exp:
        raise RuntimeError(exp)


def track_job_progress(job_id, dwnld_dir):
    from azure.batch.models import TaskState
    print("Tracking job with ID: {0}".format(job_id))
    try:
        job = batch_client.job.get(job_id)
        tasks = [t for t in batch_client.task.list(job_id)]
        while True:
            completed_tasks = [t for t in tasks if t.state == TaskState.completed]
            errored_tasks = [t for t in completed_tasks if t.execution_info.exit_code != 0]
            if len(tasks) == 0:
                percentage = 0
            else:
                percentage = (100 * len(completed_tasks)) / len(tasks)
            print("Running - {}%".format(percentage))
            if errored_tasks:
                print("    - Warning: some tasks have failed.")

            _track_completed_outputs(job_id, dwnld_dir)
            if _check_job_stopped(job):
                return # Job complete

            time.sleep(10)
            job = batch_client.job.get(job_id)
            tasks = [t for t in batch_client.task.list(job_id)]
    except KeyboardInterrupt:
        raise RuntimeError("Monitoring aborted.")

def convert_utc_expireson_to_local_timezone_naive(token):
    #the standard token expireson format which the various AAD libraries expect / return is a vanilla datetime string, in local time and timezone naive (no tz specified)
    localtz = dateutil.tz.tzlocal()
    expireson_utc = dateparse(token['expiresOnUTC']).replace(tzinfo = dateutil.tz.gettz('UTC'))
    expireson_local = expireson_utc.astimezone(dateutil.tz.tzlocal())
    expireson_local_tz_naive = expireson_local.replace(tzinfo = None)
    token['expiresOn'] = str(expireson_local_tz_naive)
    del token['expiresOnUTC']

def need_to_refresh_auth_tokens(auth_token_list):

    currentTime = datetime.datetime.now()

    tokenRefreshThresholdSeconds = 5 * 60

    for token in auth_token_list:
        if (dateparse(token['expiresOn']) - currentTime).total_seconds() < tokenRefreshThresholdSeconds:
            return True
    return False

def refresh_auth_tokens(mgmt_token, batch_token):

    context = adal.AuthenticationContext(aadAuthorityHostUrl + '/' + aadTenant, api_version=None)

    mgmt_auth_token = context.acquire_token_with_refresh_token(
        mgmt_token['refreshToken'],
        aadClientId,
        mgmtAadResource)

    batch_auth_token =  context.acquire_token_with_refresh_token(
        batch_token['refreshToken'], 
        aadClientId,
        batchAadResource)
    
    return mgmt_auth_token, batch_auth_token

def call(command, *args, **kwargs):
    """Wrap all Batch and Storage API calls in order to handle errors.
    Some errors we anticipate and raise without a dialog (e.g. PoolNotFound).
    Others we raise and display to the user.
    """
    try:
        return command(*args, **kwargs)
    except BatchErrorException as exp:
        if exp.error.code in ACCEPTED_ERRORS:
            print "Call failed: {}".format(exp.error.code)
            raise
        else:
            message = exp.error.message.value
            if exp.error.values:
                message += "Details:\n"
                for detail in exp.error.values:
                    message += "{}: {}".format(detail.key, detail.value)
            raise ValueError(message)
    except Exception as exp:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        raise ValueError("Error: {0}".format(exp))


def _authenticate(cfg_path):
    global batch_client, storage_client
    cfg = ConfigParser.ConfigParser()
    try:
        cfg.read(cfg_path)

        #TODO refactor all this to share code / functions with "config"

        subscription_id = cfg.get('AzureBatch', 'subscription_id')
        batch_url = cfg.get('AzureBatch', 'batch_url')

        mgmt_auth_token = json.loads(cfg.get('AzureBatch', 'mgmt_auth_token'))
        convert_utc_expireson_to_local_timezone_naive(mgmt_auth_token)

        batch_auth_token = json.loads(cfg.get('AzureBatch', 'batch_auth_token'))
        convert_utc_expireson_to_local_timezone_naive(batch_auth_token)

        if need_to_refresh_auth_tokens([mgmt_auth_token, batch_auth_token]):
            mgmt_auth_token, batch_auth_token = refresh_auth_tokens(mgmt_auth_token, batch_auth_token)

        mgmtCredentials = AADTokenCredentials(mgmt_auth_token)
        batchCredentials = AADTokenCredentials(batch_auth_token)

        storage_account_resource_id = cfg.get('AzureBatch', 'storage_account_resource_id')

        parsedStorageAccountId = msrestazuretools.parse_resource_id(storage_account_resource_id)
        storage_account = parsedStorageAccountId['name']

        storage_mgmt_client = StorageManagementClient(mgmtCredentials, subscription_id)

        storage_key = call(storage_mgmt_client.storage_accounts.list_keys, parsedStorageAccountId['resource_group'], storage_account).keys[0].value

        storage_client = storage.BlockBlobService(
            storage_account,
            storage_key)

        batch_client = batch.BatchExtensionsClient(batchCredentials, 
            base_url=batch_url,
            storage_client=storage_client)
        try:
            batch_client.threads = cfg.get("AzureBatch", "threads")
        except ConfigParser.NoOptionError:
            batch_client.threads = 20
    except (EnvironmentError, ConfigParser.NoOptionError, ConfigParser.NoSectionError) as exp:
        raise ValueError("Failed to authenticate.\n"
                         "Using Maya configuration file: {}\n"
                         "Error: {}".format(cfg_path, exp))


if __name__ == "__main__":
    try:
        lib_path = sys.argv[4].decode('utf-8')
        sys.path.append(lib_path)
        print("Appending path {0}".format(lib_path))

        import azure.storage.blob as storage
        import azure.batch_extensions as batch
        from azure.batch.batch_auth import SharedKeyCredentials

        from msrestazure.azure_active_directory import AdalAuthentication
        from msrestazure.azure_active_directory import AADTokenCredentials
        import msrestazure.tools as msrestazuretools

        from azure.mgmt.resource.subscriptions import SubscriptionClient
        from azure.mgmt.batch import BatchManagementClient
        from azure.mgmt.storage import StorageManagementClient

        data_path = sys.argv[1].decode('utf-8')
        job_id = sys.argv[2]
        download_dir = sys.argv[3].decode('utf-8')

        _check_valid_dir(download_dir)
        _authenticate(data_path) 

        EXIT_STRING = ""
        track_job_progress(job_id, download_dir)

    except (RuntimeError, ValueError) as exp:
        EXIT_STRING = exp

    except Exception as exp:
        EXIT_STRING = "An unexpected exception occurred: {0}".format(exp)

    finally:
        try:
            input = raw_input
        except NameError:
            pass
        print('\n' + str(EXIT_STRING))
        if input(header("Press 'enter' to exit")):
            sys.exit()