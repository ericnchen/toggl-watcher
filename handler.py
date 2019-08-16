# -*- coding: utf-8 -*-
import base64
import datetime
import json
import logging
import os
import pathlib

import requests

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# shim env; won't be needed in real deployment
for k, v in json.load(pathlib.Path("credentials.json").open(encoding="utf-8")).items():
    os.environ[k.upper()] = v


class PushcutHandler:
    def __init__(self, token: str) -> None:
        self._auth_token = token

    def push_notification(self, **kwargs):
        r = requests.post(
            "https://api.pushcut.io/v1/notifications/Hello",
            json=kwargs,
            headers={"API-Key": self._auth_token},
        )
        logger.debug(f"Pushcut: {r.json()['message']}")
        return r


class TogglHandler:
    def __init__(self, token: str) -> None:
        self._auth_token = base64.b64encode(f"{token}:api_token".encode()).decode()

    def get_current_entry(self):
        r = requests.get(
            "https://www.toggl.com/api/v8/time_entries/current",
            headers={"Authorization": "Basic " + self._auth_token},
        )
        data = r.json()["data"]
        return TogglEntry(data)


class TogglEntry:
    def __init__(self, data: dict) -> None:
        self._data = data

    @property
    def description(self) -> str:
        """Description of the entry."""
        return self._data["description"]

    @property
    def duration(self) -> int:
        """Duration of the entry in minutes."""
        return int((datetime.datetime.now().timestamp() + self._data["duration"]) / 60)


def lambda_function(event, context):
    toggl = TogglHandler(os.environ["TOGGL_API_TOKEN"])
    entry = toggl.get_current_entry()

    try:
        duration = entry.duration
        threshold = 5  # 60  # Minutes
        if duration > threshold:
            logger.debug(f"Duration threshold met ({duration} > {threshold})")
            pc_body = {
                "text": f"{entry.description} has been running for {duration} minutes.",
                "actions": [
                    {"name": "Stop timer", "shortcut": "Stop Current Toggl Timer"},
                    {"name": "Do nothing"},
                ],
            }
        else:
            logger.debug(f"Duration threshold not met ({duration} < {threshold})")
            return {
                "headers": {"Content-Type": "application/json"},
                "isBase64Encoded": False,
                "statusCode": 200,
                "body": json.dumps({}),
            }

    except TypeError:
        logger.debug("No Toggl entry")
        pc_body = {
            "text": "Tap to open Toggl or pull down for more options.",
            "defaultAction": {"name": "Open Toggl", "url": "toggl://"},
            "actions": [
                {"name": "Open Toggl", "url": "toggl://"},
                {"name": "Do nothing"},
            ],
        }

    ph = PushcutHandler(os.environ["PUSHCUT_API_TOKEN"])
    r = ph.push_notification(title="Toggl Watcher", **pc_body)

    return {
        "headers": {"Content-Type": "application/json"},
        "isBase64Encoded": False,
        "statusCode": r.status_code,
        "body": json.dumps(r.json()),
    }


if __name__ == "__main__":
    lambda_function(None, None)
