# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import webbrowser
import ConfigParser
import time
import sys
import os
import re
import threading

batch_client = None
storage_client = None
header_line_length = 50


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


def _authenticate(cfg_path):
    global batch_client, storage_client
    cfg = ConfigParser.ConfigParser()
    try:
        cfg.read(cfg_path)
        credentials = SharedKeyCredentials(
                cfg.get("AzureBatch", "batch_account"),
                cfg.get("AzureBatch", "batch_key"))
        storage_client = storage.BlockBlobService(
            cfg.get("AzureBatch", "storage_account"),
            cfg.get("AzureBatch", "storage_key"))
        batch_client = batch.BatchExtensionsClient(
            credentials, base_url=cfg.get("AzureBatch", "batch_url"),
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
        sys.path.append(sys.argv[4])
        print("Appending path {0}".format(sys.argv[4]))

        import azure.storage.blob as storage
        import azure.batch_extensions as batch
        from azure.batch.batch_auth import SharedKeyCredentials
        data_path = sys.argv[1]
        job_id = sys.argv[2]
        download_dir = sys.argv[3]

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