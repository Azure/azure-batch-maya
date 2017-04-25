#-------------------------------------------------------------------------
#
# Azure Batch Maya Plugin
#
# Copyright (c) Microsoft Corporation.  All rights reserved.
#
# The MIT License (MIT)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the ""Software""), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED *AS IS*, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
#--------------------------------------------------------------------------

import webbrowser
import ConfigParser
import time
import sys
import os
import re


batch_client = None
storage_client = None
is_thumnail = re.compile("framethumb_[\d\-]+.png")
is_log = re.compile("frame_[\d\-]+.log")


def header(header):
    header_chars = len(header)
    total_len = 50
    dashes = total_len - header_chars
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

def _download_output(container, blob_name, output_path, size):
    def progress(data, total):
        try:
            percent = float(data)*100/float(size) 
            sys.stdout.write('    Downloading... {0}%\r'.format(int(percent)))
        except:
            sys.stdout.write('    Downloading... %\r')
        finally:
            sys.stdout.flush()

    print("Downloading task output: {}".format(blob_name))
    storage_client.get_blob_to_path(container, blob_name, output_path, progress_callback=progress)
    print("    Output download successful.\n")

def _track_completed_tasks(container, dwnld_dir):
    try:
        job_outputs = storage_client.list_blobs(container)
        for output in job_outputs:
            if is_log.match(output.name):
                output_file = os.path.join(dwnld_dir, "logs", output.name)
            elif is_thumnail.match(output.name) or output.name == "Parameters.json":
                continue
            else:
                output_file = os.path.join(dwnld_dir, output.name)
        
            if not os.path.isfile(output_file):
                _download_output(container, output.name, output_file, output.properties.content_length)

    except (TypeError, AttributeError, KeyError) as exp:
        raise RuntimeError("Failed {0}".format(exp))


def _check_job_stopped(job):
    """
    Checks job for failure or completion.

    :Args:
        - job (:class:`batchapps.SubmittedJob`): an instance of the current
            SubmittedJob object.

    :Returns:
        - A boolean indicating True if the job completed, or False if still in
            progress.
    :Raises:
        - RuntimeError if the job has failed, or been cancelled.
    """

    stopped_status = [
        batch.models.JobState.disabling,
        batch.models.JobState.disabled,
        batch.models.JobState.terminating,
        batch.models.JobState.deleting
        ]
    running_status = [
        batch.models.JobState.active,
        batch.models.JobState.enabling
        ]

    try:
        if job.state in stopped_status:
            print(header("Job has stopped"))
            print("Job status: {0}".format(job.state))
            raise RuntimeError("Job is no longer running. Status: {0}".format(job.state))

        elif job.state == batch.models.JobState.completed:
            print(header("Job has completed"))
            return True

        elif job.state in running_status:
            return False

    except AttributeError as exp:
        raise RuntimeError(exp)

def track_job_progress(id, container, dwnld_dir):
    print("Tracking job with ID: {0}".format(id))
    try:
        job = batch_client.job.get(id)
        tasks = [t for t in batch_client.task.list(id)]
        
        while True:
            completed_tasks = [t for t in tasks if t.state == batch.models.TaskState.completed]
            errored_tasks = [t for t in completed_tasks if t.execution_info.exit_code != 0]
            if len(tasks) == 0:
                percentage = 0
            else:
                percentage = (100 * len(completed_tasks)) / len(tasks)
            print("Running - {}%".format(percentage))
            if errored_tasks:
                print("    - Warning: some tasks have completed with a non-zero exit code.")

            _track_completed_tasks(container, dwnld_dir)

            if _check_job_stopped(job):
                return # Job complete

            time.sleep(10)
            job = batch_client.job.get(id)
            print(job.job_preparation_task.command_line)
            for r in job.job_preparation_task.resource_files:
                print(r.blob_source)
            tasks = [t for t in batch_client.task.list(id)]

    except (TypeError, AttributeError) as exp:
        raise RuntimeError("Error occured: {0}".format(exp))

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
        batch_client = batch.BatchServiceClient(
            credentials, base_url=cfg.get("AzureBatch", "batch_url"))
        storage_client = storage.BlockBlobService(
            cfg.get("AzureBatch", "storage_account"),
            cfg.get("AzureBatch", "storage_key"),
            endpoint_suffix="core.windows.net")
    except (EnvironmentError, ConfigParser.NoOptionError, ConfigParser.NoSectionError) as exp:
        raise ValueError("Failed to authenticate using Maya configuration {0}".format(cfg_path))

if __name__ == "__main__":
    try:
        sys.path.append(sys.argv[5])
        print("Appending path {0}".format(sys.argv[5]))

        import azure.storage.blob as storage
        import azure.batch as batch
        from azure.batch.batch_auth import SharedKeyCredentials
        data_path = sys.argv[1]
        job_id = sys.argv[2]
        download_dir = sys.argv[3]
        container = sys.argv[4]

        _check_valid_dir(download_dir)
        _authenticate(data_path) 

        EXIT_STRING = ""
        track_job_progress(job_id, container, download_dir)

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