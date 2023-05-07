#! /usr/bin/env python3

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

logging.info("Starting Furk-Downloader script")

retry = 0

# Iterate through all .magnet files in the torrents_path directory
for filename in glob.glob(os.path.join(torrents_path, '*.magnet')):
    logging.info(f"Processing {filename}")
    with open(filename, 'r') as f:
        magnet = f.read().rstrip('\n')
    tor = Torrent.from_magnet(magnet)
    payload = {'info_hash': tor.info_hash, 'api_key': furk_api}
    r = requests.get('https://www.furk.net/api/dl/info', params=payload)
    data = r.json()

    # Check if the torrent is available on Furk
    if data["torrent"]["dl_status"] == 0:
        retry += 1
        if retry >= 3:
            logging.warning(f"Unable to find {filename}, removing from queue.")
            os.remove(filename)
        else:
            logging.warning(f"Torrent not available on Furk for {filename}, retrying in 5 minutes")
            time.sleep(60 * 5)
            continue
    else:
        retry = 0

    logging.info(f"Torrent found on Furk for {filename}")

    # Get download link and file information from Furk
    furk_id = data["id"]
    file_url = f'https://www.furk.net/api/dl/link?api_key={furk_api}&id={furk_id}&t_files=1'
    r = requests.get(file_url)
    data = r.json()
    strmurl = []
    title = []

    # Filter video files from Furk's file list
    video_file_types = ["video/mp4", "video/x-matroska", "video/avi", "video/mpeg", "video/quicktime", "video/x-msvideo", "video/x-ms-wmv"]
    for x in range(len(data["t_files"])):
        if data["t_files"][x]["ct"] in video_file_types:
            strmurl.append(data["t_files"][x]["url_dl"])
            title.append(data["t_files"][x]["name"])
        else:
            continue

    logging.info(f"Filtered video files for {filename}")

    # Process each video file
    for x in range(len(strmurl)):
        try:
            # Guess metadata of the video file
            metadata = guessit(str(title[x + 1].text))

            # Set the path and episode name based on the metadata type (episode or movie)
            if metadata.get('type') == 'episode':
                path = f'{completed_path}/{metadata.get("title")} - S{metadata.get("season")}E{metadata.get("episode")} - [{metadata.get("source")}-{metadata.get("screen_size")}]'
                episode = f'{metadata.get("title")} - S{metadata.get("season")}E{metadata.get("episode")} - [{metadata.get("source")} - {metadata.get("source")} - {metadata.get("screen_size")}]'
            elif metadata.get('type') == 'movie':
                path = f'{completed_path}/{os.path.splitext(os.path.basename(filename))[0]}'
                episode = metadata.get('title')
            else:
                continue

            logging.info(f"Processing video file {episode}")

            # Create the destination directory if it doesn't exist
            if not os.path.exists(path):
                os.makedirs(path)

            # Write the .strm file with the video URL
            strmfile = f'{path}/{episode}.strm'
            with open(strmfile, 'w') as f:
                f.write(strmurl[x])

            logging.info(f"Created .strm file for {episode}")

            # Check for subtitles and download them if available
            subtitle_url = ""
            subtitle_filename = f'{os.path.splitext(os.path.basename(strmurl[x]))[0]}.eng.srt'
            for t_file in data["t_files"]:
                if t_file["name"] == subtitle_filename:
                    subtitle_url = t_file["url_dl"]
                    break

            # Write the subtitle file if found
            if subtitle_url:
                subtitle_path = f'{path}/{subtitle_filename}'
                with open(subtitle_path, 'wb') as f:
                    f.write(requests.get(subtitle_url).content)
                logging.info(f"Downloaded subtitle for {episode}")

            # Update Sonarr for TV episodes
            if sonarr_key and metadata.get('type') == 'episode':
                payload = {'apikey': sonarr_key, 'path': path}
                r = requests.post(f'{sonarr_address}/api/command', json={'name': 'downloadedepisodesscan', 'path': path})
                if r.status_code != 201:
                    logging.warning(f"Unable to update Sonarr for {episode}. Response: {r.text}")
                else:
                    logging.info(f"Sonarr updated for {episode}")

            # Update Radarr for movies
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

    # Remove the .magnet file after processing
    os.remove(filename)
    logging.info(f"Removed .magnet file for {filename}")

logging.info("Furk-Downloader script completed")
