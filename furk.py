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
from logging.handlers import TimedRotatingFileHandler

from configs import furk_api
from configs import torrents_path
from configs import completed_path
from configs import TV_path
from configs import sonarr_key
from configs import sonarr_address
from configs import radarr_key
from configs import radarr_address
from configs import permissions_change
 
try:backupCount
 logging.basicConfig(handlers=[logging.FileHandler("/config/home-assistant.log"),TimedRotatingFileHandler("/config/Furk-Stream/furk.log", when="midnight", interval=1, backupCount=7),logging.StreamHandler()],format='%(asctime)s %(levelname)s (Furk Link-Check) %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
except:
 logging.basicConfig(handlers=[TimedRotatingFileHandler("furk.log", when="midnight", interval=1, backupCount=7),logging.StreamHandler()],format='%(asctime)s %(levelname)s (Furk Link-Check) %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')

sonarr_url = sonarr_address + '/api/{}?apikey=' + sonarr_key
radarr_url = radarr_address + '/api/{}?apikey=' + radarr_key

timeout = 0
processed = 0 
retry = 0

for filename in glob.glob(os.path.join(torrents_path, '*.torrent')): #converts torrents to magnet links
      torrent = Torrent.from_file(filename)
      with open(filename + ".magnet", 'w') as f:
       f.write(torrent.magnet_link)
      os.remove(filename)
        


for filename in glob.glob(os.path.join(torrents_path, '*.magnet')): #opens each magnet link
      with open(filename, 'r') as f:
        magnet = f.read()
        logging.info("Uploading \""+((filename.rsplit("/")[-1]).rsplit(".",1)[0])+"\" to Furk")
        
        try:
            base_url = 'https://www.furk.net/api/dl/add?url={}&api_key={}' #tries to add magnet link to furk
            data = (requests.get(base_url.format(magnet,furk_api))).json()
        except:
            logging.error("Unable to get valid furk response for this torrent.") #logs if no response from furk
            logging.error(str(data))
            continue

        try:
         files = data["files"][0] #checks api response, command will succeed if download has completed
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
            xspfurl = urllib.request.urlopen(files["url_pls"]) #checks api response for a playlist file, command will succeed if download has completed
          except:
            logging.warning("furk file is not yet ready for download")
            retry += 1
          else: #if ready for download than runs the playlist file through beautiful soup to parse the HTML and get the details about the file
            xspf = xspfurl.read()
            soup = BeautifulSoup(xspf, "html5lib")
            title = soup('title')
            strmurl = soup('location')

            try:
                for x in range(len(strmurl)): #runs through all the URLs in the playlist in case there are many len(strmurl) should give the size of the list of urls
                    try: #gets further details about the file using guessit library
                        metadata = guessit(str(title[x+1].text))
                        if metadata.get('type') == 'episode':
                            path = completed_path + '/' + str(metadata.get('title')) + ' - ' + 'S' + str(metadata.get('season')) + "E" + str(metadata.get('episode')) + ' - [' + str(metadata.get('source')) + '-' + str(metadata.get('screen_size')) + ']'
                            episode = str(metadata.get('title')) + ' - ' + 'S' + str(metadata.get('season')) + 'E' + str(metadata.get('episode')) + ' - [' + str(metadata.get('source')) + ' - ' + str(metadata.get('screen_size')) + ']'
                            if len(strmurl) > 1:
                                logging.info("Episode processing " + episode)
                        if metadata.get('type') == 'movie':
                            path = completed_path + '/' + ((filename.rsplit("/")[-1]).rsplit(".",1)[0])
                            episode = str(metadata.get('title'))
                        try:
                            os.mkdir(path)
                        except FileExistsError:
                            pass
                        strm = open(path+'/'+ episode +'.strm', 'w')
                        strm.write(strmurl[x].string) #writes the strm file with the correct data
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
                    if permissions_change:
                     exec(permissions_change)                    
                    if metadata.get('type') == 'episode': #updates radarr/sonarr to advise that episode is ready
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
