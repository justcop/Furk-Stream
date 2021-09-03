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

try:
 logging.basicConfig(handlers=[logging.FileHandler("/config/home-assistant.log"),TimedRotatingFileHandler(os.path.dirname(__file__) + "furk.log", when="midnight", interval=1, backupCount=7),logging.StreamHandler()],format='%(asctime)s %(levelname)s (Furk Link-Check) %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
except:
 logging.basicConfig(handlers=[TimedRotatingFileHandler(os.path.dirname(__file__) + "furk.log", when="midnight", interval=1, backupCount=7),logging.StreamHandler()],format='%(asctime)s %(levelname)s (Furk Link-Check) %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')

sonarr_url = sonarr_address + '/api/{}?apikey=' + sonarr_key
radarr_url = radarr_address + '/api/{}?apikey=' + radarr_key

timeout = 0
processed = 0 
retry = 0

try:
            base_url = 'https://www.furk.net/api/file/get?api_key={}' #gets list of files
            data = (requests.get(base_url.format(furk_api))).json()
except:
            logging.error("Unable to get valid furk response for this torrent.") #logs if no response from furk
            logging.error(str(data))
            continue

for file in data["files"]:        
  if str(file["url_dl"]) = str(sys.argv[1])
  
  try:
            xspfurl = urllib.request.urlopen(file["url_pls"]) #checks api response for a playlist file, command will succeed if download has completed
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
                    #os.system('chown -R 1001:1002 /share/downloads')
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
