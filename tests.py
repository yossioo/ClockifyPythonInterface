#!/usr/bin/python
import time
import os
from os import path as osp
from tqdm import tqdm
from clockify_api import ClockifyClient

API_KEY = "API_KEY-Yossi"
if osp.isfile(osp.join(os.getcwd(), API_KEY)):
    with open(API_KEY, "r") as file:
        API_KEY = file.read().strip()

client = ClockifyClient(API_KEY)
ok = client.start_new_time_entry_in_project("LAR1", "Dummy task" + client.utc_now())
if ok:
    print("Succesfully added a task")

s = 35
print(f"Sleeping {s} sec")
for _ in tqdm(range(s)):
    time.sleep(1)
ok = client.stop_current_time_entry()
if ok:
    print("succesfully stoped timer")