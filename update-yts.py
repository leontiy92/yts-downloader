from pymongo import MongoClient
import pymongo, json, os, shutil
import time, subprocess
import json
import requests
import logging
import configargparse

p = configargparse.ArgParser(default_config_files=["downloader.conf"])
p.add("-c", "--config-file", is_config_file=True, help="config file path")

p.add("--mongodb", help="MogoDB connection string", default="mongodb://127.0.0.1:27017")
p.add("--mongodb-collection", help="MogoDB collection to use", default="yts")

options = p.parse_args()

client = MongoClient(options.mongodb)
yts = client[options.mongodb_collection]
mv = yts["movies"]

def get_page(pg):
    r = requests.get(f"https://yts.mx/api/v2/list_movies.json?page={pg}")
    if r.status_code != 200:
        logging.warning(f"{pg} failed: {r.status_code}")
        return None
    j = json.loads(r.content)
    if "data" not in j:
        logging.info(f"{pg}: no data")
        return None
    j = j["data"]
    if "movies" not in j:
        logging.info(f"{pg}: no movies")
        return None
    movies = j["movies"]
    if len(movies) == 0:
        logging.info(f"{pg}: no movies")
        return None
    for m in movies:
        _id = m["id"]
        del m["id"]
        mv.update_one({"_id": _id}, {"$set": m}, upsert=True)
    return True


pg = 1
while get_page(pg):
    print(f"Page {pg}", end="\r")
    pg += 1
print("Done")
