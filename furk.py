#! /usr/bin/env python3

# Import necessary modules and packages
import os
import glob
import requests
import json
import ast
import logging
import urllib
import time
import html5lib

from guessit import guessit
from bs4 import BeautifulSoup
from torrentool.api import Torrent
from logging.handlers import TimedRotatingFileHandler

# Import configuration constants from separate file
from configs import furk_api
from configs import torrents_path
from configs import completed_path
from configs import sonarr_key
from configs import sonarr_address
from configs import radarr_key
from configs import radarr_address

# Set up logging to write logs to a file and the console
try:
    logging.basicConfig(handlers=[logging.FileHandler("/config/home-assistant.log"),
                                  TimedRotatingFileHandler("/config/Furk-Stream/furk.log", when="midnight", interval=1, backupCount=7),
                                  logging.StreamHandler()],
                        format='%(asctime)s %(levelname)s (Furk-Downloader) %(message)s',
                        level=logging.INFO,
                        datefmt='%Y-%m-%d %H:%M:%S')
except FileNotFoundError:
    logging.basicConfig(handlers=[TimedRotatingFileHandler("furk.log", when="midnight", interval=1, backupCount=7),
                                  logging.StreamHandler()],
                        format='%(asctime)s %(levelname)s (Furk-Downloader) %(message)s',
                        level=logging.INFO,
                        datefmt='%Y-%m-%d %H:%M:%S')

# Set up URLs for Sonarr and Radarr API requests
sonarr_url = f"{sonarr_address}/api/{{}}?apikey={sonarr_key}"
radarr_url = f"{radarr_address}/api/{{}}?apikey={radarr_key}"

# Set up variables for tracking processed files and retries
timeout = 0
processed = 0
retry = 0


def convert_torrents_to_magnets():
    for filename in glob.glob(os.path.join(torrents_path, '*.torrent')):
        torrent = Torrent.from_file(filename)
        with open(f"{filename}.magnet", 'w') as f:
            f.write(torrent.magnet_link)
        os.remove(filename)


def process_magnet_files():
    global processed
    global retry

    for filename in glob.glob(os.path.join(torrents_path, '*.magnet')):
        with open(filename, 'r') as f:
            magnet = f.read()
            logging.info(f'Uploading "{(filename.rsplit("/")[-1]).rsplit(".", 1)[0]}" to Furk')

            # Try to add magnet link to Furk
            try:
                base_url = f'https://www.furk.net/api/dl/add?url={{}}&api_key={furk_api}'
                data = (requests.get(base_url.format(magnet, furk_api))).json()
            except requests.exceptions.RequestException as e:
                # Log if no response from Furk
                logging.error("Unable to get valid Furk response for this torrent.")
                logging.error(str(data))
                continue

            # Check API response for a file object to see if download has completed
            try:
                files = data["files"][0]
                logging.info(f'Checking {data["files"][0]["name"]} in Furk')
            except KeyError:
                try:
                    if data["torrent"]["dl_status"] == "active" or "finished":
                        pass
                except KeyError:
                    # Log if API response is unexpected or does not contain a file object
                    logging.error("Furk returned unexpected response, without file data")
                    logging.error(str(data))
                    continue
                else:
                    # Log if file is not yet ready for download and increment retry counter
                    logging.warning(f'Furk file "{(filename.rsplit("/")[-1]).rsplit(".", 1)[0]}" is not yet ready for download')
                    retry += 1
            else:
                # Try to get playlist file from Furk API response
            logging.warning("Unable to update Sonarr or Radarr")
            logging.error(e)

if __name__ == "__main__":
    convert_torrents_to_magnets()
    process_magnet_files()

                try:
                    xspfurl = urllib.request.urlopen(files["url_pls"])
                except urllib.error.URLError as e:
                    # Log if playlist file is not yet available and increment retry counter
                    logging.warning("Furk file is not yet ready for download")
                    retry += 1
                else:
                    # Parse playlist file using BeautifulSoup and extract details using guessit
                    xspf = xspfurl.read()
                    soup = BeautifulSoup(xspf, "html5lib")
                    title = soup('title')
                    strmurl = soup('location')

                    try:
                        for x in range(len(strmurl)):
                            try:
                                metadata = guessit(str(title[x + 1].text))
                                process_metadata(metadata, strmurl, x, filename)
                            except Exception as e:
                                # Log if unable to write a valid .strm file and log the error
                                logging.error("Unable to write a valid .strm file")
                                logging.error(e)
                    except Exception as e:
                        # Log if unable to process entire playlist file and log the error
                        logging.error("Unable to process entire .strm file")
                        logging.error(e)

    logging.info(f"{processed} files have been processed.")


def process_metadata(metadata, strmurl, x, filename):
    global processed

    if metadata.get('type') == 'episode':
        path = f'{completed_path}/{metadata.get("title")} - S{metadata.get("season")}E{metadata.get("episode")} - [{metadata.get("source")}-{metadata.get("screen_size")}]'
        episode = f'{metadata.get("title")} - S{metadata.get("season")}E{metadata.get("episode")} - [{metadata.get("source")} - {metadata.get("screen_size")}]'
    elif metadata.get('type') == 'movie':
        path = f'{completed_path}/{(filename.rsplit("/")[-1]).rsplit(".", 1)[0]}'
        episode = metadata.get('title')

    try:
        os.mkdir(path)
    except FileExistsError:
        pass

    with open(f'{path}/{episode}.strm', 'w') as strm:
        strm.write(strmurl[x].string)

    processed += 1

    # Log if processing is complete and remove the .magnet file
    try:
        logging.info(f'Completed processing {data["files"][0]["name"]}')
        os.remove(filename)

        # Update Sonarr or Radarr to advise that episode is ready
        if metadata.get('type') == 'episode':
            data = {'name': 'DownloadedEpisodesScan', 'path': path}
            response = (requests.post(sonarr_url.format('command'), json=data)).json()
        elif metadata.get('type') == 'movie':
            data = {'name': 'DownloadedMoviesScan', 'path': path}
            response = (requests.post(radarr_url.format('command'), json=data)).json()
    except Exception as e:
        try:
            logging.info(response['body']['completionMessage'])
        except KeyError:
            # Log if unable to update Sonarr or Radarr
           
