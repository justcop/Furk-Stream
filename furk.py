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

from guessit import guessit
from bs4 import BeautifulSoup
from torrentool.api import Torrent

from configs import furk_api
from configs import torrents_path
from configs import completed_path
from configs import TV_path
from configs import sonarr_key
from configs import sonarr_address
from configs import radarr_key
from configs import radarr_address

logging.basicConfig(handlers=[logging.FileHandler("/config/home-assistant.log"),logging.FileHandler("/config/furk.log"),logging.StreamHandler()],format='%(asctime)s %(levelname)s (Furk) %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')



sonarr_url = sonarr_address + '/api/{}?apikey=' + sonarr_key
radarr_url = radarr_address + '/api/{}?apikey=' + radarr_key

timeout = 0



processed = 0
retry = 0

for filename in glob.glob(os.path.join(torrents_path, '*.torrent')):
      torrent = Torrent.from_file(filename)
      with open(filename + ".magnet", 'w') as f:
       f.write(torrent.magnet_link)
      os.remove(filename)
        


for filename in glob.glob(os.path.join(torrents_path, '*.magnet')):
      with open(filename, 'r') as f:
        magnet = f.read()
        logging.info("Uploading \""+((filename.rsplit("/")[-1]).rsplit(".",1)[0])+"\" to Furk")
        
        try:
            base_url = 'https://www.furk.net/api/dl/add?url={}&api_key={}'
            data = (requests.get(base_url.format(magnet,furk_api))).json()
        except:
            logging.error("Unable to get valid furk response for this torrent.")
            logging.error(data)
            continue

        try:
         files = data["files"][0]
         logging.info("Checking "+data["files"][0]["name"]+" in Furk")
        except:
            try:
                if data["torrent"]["dl_status"] == "active" or "finished":
                    pass
            except:
                logging.error("furk returned unexpected response, without file date")
                logging.error(str(data))
                continue
            else:
                logging.warning("furk file \""+((filename.rsplit("/")[-1]).rsplit(".",1)[0])+"\" is not yet ready for download")
                retry += 1
        else:
          try:
            xspfurl = urllib.request.urlopen(files["url_pls"])
          except:
            logging.warning("furk file is not yet ready for download")
            retry += 1
          else:
            xspf = xspfurl.read()
            soup = BeautifulSoup(xspf, "html5lib")
            title = soup('title')
            strmurl = soup('location')

            try:
                for x in range(len(strmurl)):
                    try:
                        metadata = guessit(str(title[x+1].text))
                        if metadata.get('type') == 'episode':
                            path = completed_path + '/' + str(metadata.get('title')) + ' - ' + 'S' + str(metadata.get('season')) + "E" + str(metadata.get('episode')) + ' - [' + str(metadata.get('source')) + '-' + str(metadata.get('screen_size')) + ']'
                            episode = str(metadata.get('title')) + ' - ' + 'S' + str(metadata.get('season')) + 'E' + str(metadata.get('episode')) + ' - [' + str(metadata.get('source')) + ' - ' + str(metadata.get('screen_size')) + ']'
                            if len(strmurl) > 1:
                                logging.info("Episode processing " + episode)
                        if metadata.get('type') == 'movie':
                            path = completed_path + '/' + ((filename.rsplit("/")[-1]).rsplit(".",1)[0])
                            episode = str(title[x+1].text
                        try:
                            os.mkdir(path)
                        except FileExistsError:
                            pass
                        strm = open(path+'/'+ episode +'.strm', 'w')
                        strm.write(strmurl[x].string)
                        strm.close()
                        processed += 1
                    except Exception as e:
                        logging.error("Unable to write a valid strm file")
                        logging.error(e)
            except Exception as e:
                logging.error("Unable to process entire strm file")
                logging.error(e)
            else:
                try:
                    logging.info("Completed processing "+data["files"][0]["name"])
                    os.remove(filename)
                    os.system('chown -R 1001:1002 /share/downloads')
                    if metadata.get('type') == 'episode':
                        data = {'name':'DownloadedEpisodesScan','path':path}
                        response = (requests.post(sonarr_url.format('command'),json=data)).json()
                    if metadata.get('type') == 'movie':
                        data = {'name':'DownloadedMoviesScan','path':path}
                        response = (requests.post(radarr_url.format('command'),json=data)).json()
                except:
                    try:
                        logging.info(response['body']['completionMessage'])
                    finally:
                        logging.warning("Unable to update sonarr/radarr")
                        
logging.info(str(processed) + " files have been processed.")
