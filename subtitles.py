from pymongo import MongoClient
import requests, zipfile, io
from bs4 import BeautifulSoup, UnicodeDammit
from langcodes import *
import json, os
import time, subprocess
import logging
import pysubs2


class Vars:
    def __init__(self, movies=None, DL_DIR=None):
        self.movies = movies
        self.DL_DIR = DL_DIR


v = Vars()


def setup(options):
    mongo_conn_string = options.mongodb
    mongo_coll = options.mongodb_collection
    v.DL_DIR = os.path.abspath(options.download_dir)

    client = MongoClient(mongo_conn_string)
    yts = client[mongo_coll]
    v.movies = yts["movies"]


def get_subtitle_list(table):
    rows = []

    trs = table.find_all("tr")
    headerow = [td.get_text(strip=True) for td in trs[0].find_all("th")]
    if headerow:
        rows.append(headerow)
        trs = trs[1:]

    for tr in trs:
        row = []
        for td in tr.find_all("td"):
            row.append(td.get_text(strip=True))
        row[-1] = tr.find("a")["href"]
        rows.append(row)

    return rows


def find_subtitles(imdb_id):
    base_url = f"https://yts-subs.com/movie-imdb/{imdb_id}"
    logging.debug(f"{imdb_id}: downloading subtitles list from {base_url}")
    try:
        r = requests.get(base_url)
        r.raise_for_status()
        html_content = r.text
    except requests.exceptions.HTTPError as e:
        # TODO: do something useful
        logging.warn(f"{imdb_id}: got {e} downloading from {base_url}")
        return None

    soup = BeautifulSoup(html_content, "lxml")
    htmltable = soup.find("table", {"class": "table other-subs"})

    if htmltable is None:
        if html_content.find("404 ! Page Not Found"):
            logging.info(f"{imdb_id}: no subtitles")
            return []  # no subs
        assert (False, "bad parsing?")

    data = get_subtitle_list(htmltable)
    best = dict()
    for sub in data[1:]:
        # TODO: filter langueages?
        rating, lang = sub[:2]
        rating = int(rating)
        logging.info(f"{imdb_id}: found subtitle {lang} with rating {rating}")
        try:
            lc = str(find(lang))
        except Exception as e:
            # TODO
            logging.info(f"{imdb_id}: couldn't parse {lang}")
            continue

        if lc not in best:
            best[lc] = sub
        else:
            if int(sub[0]) > int(best[lc][0]):
                best[lc] = sub
            else:
                if int(sub[0]) > int(best[lc][0]):
                    best[lc] = sub

    subs = []
    for lang, data in best.items():
        s = data[-1]
        s = s[:9] + s[9 + 1 :]
        url = f"https://yifysubtitles.org{s}.zip"
        logging.debug(f"{imdb_id}: {lang} {url}")
        subs.append((lang, url))
    return subs


def make_srt(sub: str):
    # Force Unicode
    dammit = UnicodeDammit(sub)
    sub = dammit.unicode_markup

    try:
        sub = pysubs2.SSAFile.from_string(sub)
        return sub.to_string("srt")
    except Exception as e:
        logging.warn(f"got error for subtitle: {e}")
        return None

    
def download_subtitle(lang, url):
    logging.debug(f"downloading subtitle {lang} from {url}")
    try:
        r = requests.get(url)
        r.raise_for_status()
        z = zipfile.ZipFile(io.BytesIO(r.content))
    except Exception as e:
        # TODO
        logging.warn(f"Got error downloading from {url}")
        return None

    d = z.infolist()
    assert len(d) == 1

    with z.open(d[0]) as f:
        return make_srt(f.read())


def download(id: int):
    m = v.movies.find_one({"_id": id})
    slug = m["slug"]
    imdb_id = m["imdb_code"]
    logging.debug(f"{slug}: downloading subtitles; imdb-id: {imdb_id}")

    subs = []
    s = find_subtitles(imdb_id)
    if s is None:
        logging.info(f"{slug}: failed to find subtitles")
        return None
    for lang, url in s:
        # TODO: filter languages?
        logging.debug(f"{id}/{slug}: downloading subtitle {lang} from {url}")
        sub = download_subtitle(lang, url)

        if sub is None:
            logging.info(f"{id}/{slug}: failed to download subtitle {lang}")
            continue
        fname = f"{slug}.{lang}.srt"  # TODO: support other formats?
        with open(os.path.join(v.DL_DIR, fname), "w") as f:
            f.write(sub)
        subs.append(lang)
        logging.info(f"{id}/{slug}: downloaded subtitle {lang}")
        v.movies.update_one({"_id": id}, {"$addToSet": {"files.subtitles": lang}})
    return subs
