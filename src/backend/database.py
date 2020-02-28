import os
from pymongo import MongoClient
from datetime import datetime, timedelta
from time import sleep
from threading import Thread
from typing import Dict

client = MongoClient(os.getenv("MONGO_DB_CONNECT"))["project-dark"]

db_objs_state: Dict[object, datetime] = dict()



def cache_management_function(seconds: int):
  delta = timedelta(0, seconds)
  while True:
    now = datetime.now()
    global db_objs_state
    db_objs_state = {
      obj: time for obj, time in db_objs_state.items() \
        if now <= time + delta
    }
    sleep(30)

cache_management = Thread(target = cache_management_function, args = [500])
cache_management.start()
