# -*- coding: utf-8 -*-
import base64
import datetime as dt
import json
import os
import pathlib

import requests

# shim env; won't be needed in real deployment
for k, v in json.load(pathlib.Path("credentials.json").open(encoding="utf-8")).items():
    os.environ[k.upper()] = v


def main():
    tg_url = "https://www.toggl.com/api/v8/time_entries/current"
    tg_key = os.environ["TOGGL_API_TOKEN"]
    tg_akey = base64.b64encode(f"{tg_key}:api_token".encode("utf-8")).decode("utf-8")
    tg_resp = requests.get(tg_url, headers={"Authorization": f"Basic {tg_akey}"})
    tg_body = tg_resp.json()
    tg_data = tg_body["data"]

    if tg_data:
        dur_threshold = 5  # 60  # Minutes
        dur = int((dt.datetime.now().timestamp() + tg_data["duration"]) / 60)
        if dur > dur_threshold:
            pc_url = "https://api.pushcut.io/v1/notifications/Hello"
            pc_token = os.environ["PUSHCUT_API_TOKEN"]
            pc_body = {
                "text": f"{tg_data['description']} has been running for {dur} minutes.",
                "title": "Toggl Watcher",
                "actions": [
                    {"name": "keep it running", "url": "http://localhost"},
                    {"name": "stop the timer", "url": "http://localhost"},
                ],
            }
            pc_resp = requests.post(pc_url, json=pc_body, headers={"API-Key": pc_token})
            if pc_resp.status_code == 200:
                return  # message = success
            return  # message = failure
        else:
            return  # exit early w/ some kind of status or message
    else:
        pc_url = "https://api.pushcut.io/v1/notifications/Hello"
        pc_token = os.environ["PUSHCUT_API_TOKEN"]
        pc_body = {
            "text": "Time isn't being logged right now.",
            "title": "Toggl Watcher",
            "actions": [
                {"name": "track something", "url": "http://localhost"},
                {"name": "don't track anything", "url": "http://localhost"},
            ],
        }
        pc_resp = requests.post(pc_url, json=pc_body, headers={"API-Key": pc_token})
        if pc_resp.status_code == 200:
            return  # message = success
        return  # message = failure


if __name__ == "__main__":
    main()
