import aria2p
import logging
import os
import sys
from pymongo import MongoClient
import time
import subtitles
import logging
import shutil
from pathlib import Path

yts_trackers = "udp://open.demonii.com:1337/announce&udp://tracker.openbittorrent.com:80&udp://tracker.coppersurfer.tk:6969&udp://glotorrents.pw:6969/announce&udp://tracker.opentrackr.org:1337/announce&udp://torrent.gresille.org:80/announce&udp://p4p.arenabg.com:1337&udp://tracker.leechers-paradise.org:6969"


class Vars:
    def __init__(
        self,
        aria2=None,
        movies=None,
        MAX_CON=0,
        MOVIE_QUALITY="",
        DL_DIR="",
        TEMP_DIR="",
    ):
        self.aria2 = aria2
        self.movies = movies
        self.MAX_CON = MAX_CON
        self.MOVIE_QUALITY = MOVIE_QUALITY
        self.DL_DIR = DL_DIR
        self.TEMP_DIR = TEMP_DIR

v = Vars()


def setup(options):
    host = options.aria_host
    port = options.aria_port
    secret = options.aria_secret
    mongo_conn_string = options.mongodb
    mongo_coll = options.mongodb_collection
    v.MAX_CON = options.max_con_dl
    v.MOVIE_QUALITY = options.quality
    v.DL_DIR = os.path.abspath(options.download_dir)
    v.TEMP_DIR = os.path.abspath(options.temp_dir)

    logging.debug(f"setting up aria2: {host}:{port}")
    logging.debug(f"download directory: {v.DL_DIR}")
    logging.debug(f"temp directory: {v.TEMP_DIR}")

    v.aria2 = aria2p.API(aria2p.Client(host=f"http://{host}", port=port, secret=secret))

    logging.debug(f"setting up MongoDB for collection {mongo_coll}")
    client = MongoClient(mongo_conn_string)
    yts = client[mongo_coll]
    v.movies = yts["movies"]


def scan_aria():
    dls = v.aria2.get_downloads()
    active = set()
    complete = set()
    for dl in dls:
        if dl.status == "complete":
            if dl.is_metadata:
                logging.debug(f"{dl.dir.name}: meta done")
                dl.remove()
            else:
                dir = dl.dir
                id = int(dir.name)
                logging.debug(f"{id}: done")
                dl.remove()
                complete.add(id)
                handle_complete(id, dir)
        elif dl.status == "active":
            logging.debug(f"{dl.dir.name}: still active")
            active.add(int(dl.dir.name))
        elif dl.status == "error":
            logging.info(f"{dl.dir.name}: failed")
            try:
                shutil.rmtree(dl.dir)
            except FileNotFoundError:
                pass
            dl.remove()
    num_dls = len(v.aria2.get_downloads())
    logging.debug(
        f"aria queue: {num_dls}: {len(complete)} complete, {len(active)} active"
    )
    return len(v.aria2.get_downloads()), complete, active


def aria2_add(id, hash):
    magnet = f"magnet:?xt=urn:btih:{hash}&dn={id}i&tr={yts_trackers}"
    dl_dir = os.path.join(v.TEMP_DIR, f"{id}")
    return v.aria2.add_magnet(magnet, options={"dir": dl_dir})


def handle_complete(id, dir):
    m = v.movies.find_one({"_id": id})
    slug = m["slug"]
    found = False
    for root, dirs, files in os.walk(dir):
        if found:
            break
        for file in files:
            if file.endswith(".mp4"):
                # TODO: multiple movies?
                fname = os.path.join(root, file)
                new_path = os.path.join(v.DL_DIR, f"{slug}.mp4")

                Path(fname).rename(new_path)
                found = True
                logging.info(f"Done {slug}.mp4")
                break
            else:
                # TODO: handle subtitles?
                pass
    assert found
    v.movies.update_one({"_id": id}, {"$set": {"files.movie": "downloaded"}})
    shutil.rmtree(dir)


def get_hash(m):
    if "torrents" not in m:
        logging.info(f"{m.id}: no torrents")
        return None
    torrents = m["torrents"]
    candidates = []
    for t in torrents:
        if t["quality"] != v.MOVIE_QUALITY:
            # TODO: maybe download a different quality movie?
            continue
        candidates.append(t)
    if len(candidates) == 0:
        return None
    elif len(candidates) == 1:
        return candidates[0]["hash"]
    else:
        # TODO: need to decide which torrent to prefer
        return candidates[0]["hash"]


def run():
    while True:
        count, complete, active = scan_aria()
        for m in v.movies.aggregate(
            [
                {"$match": "files": {"$exists": False}}},
                {"$sample": {"size": 5}},
            ]
        ):
            _id = m["_id"]
            if m["_id"] in active or m["_id"] in complete:
                continue

            h = get_hash(m)
            if h is None:
                continue

        if count > v.MAX_CON:
            logging.info(f"{count} downloads in queue. sleeping")
            time.sleep(30)

        h = get_hash(m)
        if h is None:
            continue
        logging.info(f"{_id}/{m['slug']}: adding to aria2")
        aria2_add(_id, h)

      
