# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from msrest.exceptions import ValidationError, ClientRequestError
from azure.batch.models import BatchErrorException
import threading
try:
    from queue import Queue
except ImportError:
    from Queue import Queue
    
# pylint: disable=too-few-public-methods


def _handle_batch_exception(action):
    try:
        return action()
    except BatchErrorException as ex:
        try:
            message = ex.error.message.value
            if ex.error.values:
                for detail in ex.error.values:
                    message += "\n{}: {}".format(detail.key, detail.value)
            raise Exception(message)
        except AttributeError:
            raise Exception(ex)
    except (ValidationError, ClientRequestError) as ex:
        raise Exception(ex)


def _bulk_add_tasks(client, job_id, tasks, queue):
    added_tasks = client.add_collection(job_id, tasks)
    for task in added_tasks.value:
        queue.put(task)
    
def deploy_tasks(client, job_id, tasks):
    MAX_TASKS_COUNT_IN_BATCH = 100
    MAX_SUBMIT_THREADS = 10

    def add_task():
        start = 0
        progress_queue = Queue()
        submitting_tasks = []
        submitted_tasks = []
        while True:
            end = min(start + MAX_TASKS_COUNT_IN_BATCH, len(tasks))
            submit = threading.Thread(target=_bulk_add_tasks, args=(client, job_id, tasks[start:end], progress_queue))
            submit.start()
            submitting_tasks.append(submit)
            start = end
            if start >= len(tasks) or len(submitting_tasks) >= MAX_SUBMIT_THREADS:
                while any(s for s in submitting_tasks if s.is_alive()) or not progress_queue.empty():
                    submitted_tasks.append(progress_queue.get())
                    progress_queue.task_done()
                submitting_tasks = []
                if start >= len(tasks):
                    break
        return submitted_tasks
    _handle_batch_exception(add_task)


def get_task_counts(client, job_id):
    task_counts = {
        'active': 0,
        'running': 0,
        'completed': 0
    }

    def action():
        result = client.task.list(job_id, select='id, state')
        for task in result:
            if task.state in ['active', 'running', 'completed']:
                task_counts[task.state] += 1
            else:
                raise ValueError('Invalid task state')
        return task_counts

    return _handle_batch_exception(action)


def get_target_pool(client, job):
    def action():
        return client.get(job.pool_info.pool_id)

    if not job.pool_info:
        raise ValueError('Missing required poolInfo.')

    pool = None
    if job.pool_info.pool_id:
        pool = _handle_batch_exception(action)
    elif job.pool_info.auto_pool_specification \
            and job.pool_info.auto_pool_specification.pool:
        pool = job.pool_info.auto_pool_specification.pool
    else:
        raise ValueError('Missing required poolId or autoPoolSpecification.pool.')

    return pool
