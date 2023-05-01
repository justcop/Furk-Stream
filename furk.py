import os
import glob
import requests
import json
import ast
import logging
import urllib
import time
import html5lib
import os.path

from guessit import guessit
from bs4 import BeautifulSoup
from torrentool.api import Torrent
from logging.handlers import TimedRotatingFileHandler

from configs import furk_api
from configs import torrents_path
from configs import completed_path
from configs import sonarr_key
from configs import sonarr_address
from configs import radarr_key
from configs import radarr_address
from configs import permissions_change

# Set up logging to write logs to a file and the console
log_format = '%(asctime)s %(levelname)s (Furk-Downloader) %(message)s'
log_datefmt = '%Y-%m-%d %H:%M:%S'

if os.path.exists("/config/home-assistant.log"):
    logging.basicConfig(
        handlers=[
            logging.FileHandler("/config/home-assistant.log"),
            TimedRotatingFileHandler("/config/Furk-Stream/furk.log", when="midnight", interval=1, backupCount=7),
            logging.StreamHandler()
        ],
        format=log_format,
        level=logging.INFO,
        datefmt=log_datefmt
    )
else:
    logging.basicConfig(
        handlers=[
            TimedRotatingFileHandler("furk.log", when="midnight", interval=1, backupCount=7),
            logging.StreamHandler()
        ],
        format=log_format,
        level=logging.INFO,
        datefmt=log_datefmt
    )

retry = 0

for filename in glob.glob(os.path.join(torrents_path, '*.magnet')):
    with open(filename, 'r') as f:
        magnet = f.read().rstrip('\n')
    tor = Torrent.from_magnet(magnet)
    payload = {'info_hash': tor.info_hash, 'api_key': furk_api}
    r = requests.get('https://www.furk.net/api/dl/info', params=payload)
    data = r.json()

    if data["torrent"]["dl_status"] == 0:
        retry += 1
        if retry >= 3:
            logging.warning(f"Unable to find {filename}, removing from queue.")
            os.remove(filename)
        else:
            time.sleep(60 * 5)
            continue
    else:
        retry = 0

    furk_id = data["id"]
    file_url = f'https://www.furk.net/api/dl/link?api_key={furk_api}&id={furk_id}&t_files=1'
    r = requests.get(file_url)
    data = r.json()
    strmurl = []
    title = []
    for x in range(len(data["t_files"])):
        if data["t_files"][x]["ct"] == "video/mp4" or data["t_files"][x]["ct"] == "video/x-matroska":
            strmurl.append(data["t_files"][x]["url_dl"])
            title.append(data["t_files"][x]["name"])
        else:
            continue

    for x in range(len(strmurl)):
        try:
            metadata = guessit(str(title[x + 1].text))
            if metadata.get('type') == 'episode':
                path = f'{completed_path}/{metadata.get("title")} - S{metadata.get("season")}E{metadata.get("episode")} - [{metadata.get("source")}-{metadata.get("screen_size")}]'
                episode = f'{metadata.get("title")} - S{metadata.get("season")}E{metadata.get("episode")} - [{metadata.get("source")} - {metadata.get("source")} - {metadata.get("screen_size")}]'
            elif metadata.get('type') == 'movie':
                path = f'{completed_path}/{os.path.splitext(os.path.basename(filename))[0]}'
                episode = metadata.get('title')
            else:
                continue

            if not os.path.exists(path):
                os.makedirs(path)

            strmfile = f'{path}/{episode}.strm'
            with open(strmfile, 'w') as f:
                f.write(strmurl[x])

            subtitle_url = ""
            subtitle_filename = f'{os.path.splitext(os.path.basename(strmurl[x]))[0]}.eng.srt'
            for t_file in data["t_files"]:
                if t_file["name"] == subtitle_filename:
                    subtitle_url = t_file["url_dl"]
                    break

            if subtitle_url:
                subtitle_path = f'{path}/{subtitle_filename}'
                with open(subtitle_path, 'wb') as f:
                    f.write(requests.get(subtitle_url).content)

            if permissions_change:
                os.chmod(path, 0o777)
                os.chmod(strmfile, 0o777)
                if subtitle_url:
                    os.chmod(subtitle_path, 0o777)

            if sonarr_key and metadata.get('type') == 'episode':
                payload = {'apikey': sonarr_key, 'path': path}
                r = requests.post(f'{sonarr_address}/api/command', json={'name': 'downloadedepisodesscan', 'path': path})
                if r.status_code != 201:
                    logging.warning(f"Unable to update Sonarr for {episode}. Response: {r.text}")
                else:
                    logging.info(f"Sonarr updated for {episode}")

            if radarr_key and metadata.get('type') == 'movie':
                payload = {'apikey': radarr_key, 'path': path}
                r = requests.post(f'{radarr_address}/api/command', json={'name': 'downloadedmoviescan', 'path': path})
                if r.status_code != 201:
                    logging.warning(f"Unable to update Radarr for {episode}. Response: {r.text}")
                else:
                    logging.info(f"Radarr updated for {episode}")

        except Exception as e:
            logging.error(f"Error processing {filename}: {e}")
            continue

    os.remove(filename)
