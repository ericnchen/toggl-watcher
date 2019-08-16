# -*- coding: utf-8 -*-
import base64
import datetime
import logging
import os
import urllib.parse

# import requests
from botocore.vendored import requests

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def check_status():
    """Check if something is being logged. An empty dict returned means no.

    The possible keys in the output are `id`, `duration`, and `description`.

    * If `id` exists, then something is being tracked.
    * `description` is the name of the entry being tracked if it has one.
    * `duration` is a number used to get the duration of the entry.
    """
    logger.debug("Starting the check_status() routine.")

    url = "https://www.toggl.com/api/v8/time_entries/current"
    token = os.environ["TOGGL_API_TOKEN"]
    auth_token = base64.b64encode(f"{token}:api_token".encode()).decode()
    resp = requests.get(url, headers={"Authorization": "Basic " + auth_token})

    cols = "id", "duration", "description"
    status = {k: v for k, v in (resp.json()["data"] or {}).items() if k in cols}
    logger.debug(f"{'Something' if 'id' in status else 'Something'} is being tracked.")

    return status


def handle_status(status, threshold=1):
    logger.debug("Starting the handle_status() routine.")

    if "id" not in status:
        return trigger_pushcut("Toggl Watcher - Nothing Running")

    duration = int((datetime.datetime.now().timestamp() + status["duration"]) / 60)
    entry_name = status.get("description", str(status["id"]))

    if duration > threshold:
        data = {"text": f"{entry_name} has been running for {duration} minutes."}
        return trigger_pushcut("Toggl Watcher - Threshold Met", data=data)

    else:
        return 200


def trigger_pushcut(notification: str, data=None) -> int:
    """Trigger a Pushcut notification.

    Args:
        notification: The name of the notification to trigger.
        data (optional): Additional info for the Pushcut API.
    """
    headers = {"API-Key": os.environ["PUSHCUT_API_TOKEN"]}
    url = f"https://api.pushcut.io/v1/notifications/{urllib.parse.quote(notification)}"
    return requests.post(url, json=data, headers=headers).status_code


# noinspection PyUnusedLocal
def periodic_check(event, context):
    logger.debug("Starting the periodic_check() routine.")

    status = check_status()
    status_code = handle_status(status, threshold=event.get("threshold", 60))

    return {"statusCode": status_code}


# noinspection PyUnusedLocal
def stop(event, context):
    logger.debug("Starting the stop_current() routine.")

    status = check_status()

    if "id" in status:
        url = f"https://www.toggl.com/api/v8/time_entries/{status['id']}/stop"
        token = os.environ["TOGGL_API_TOKEN"]
        auth_token = base64.b64encode(f"{token}:api_token".encode()).decode()
        r = requests.put(url, headers={"Authorization": "Basic " + auth_token})
        status_code = r.status_code
    else:
        status_code = 200

    return {"statusCode": status_code}


if __name__ == "__main__":
    stop({}, None)
    # periodic_check({}, None)
