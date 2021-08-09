#! /usr/bin/env python3

import urllib.request, urllib.error, urllib.parse
import os
import pickle
import datetime
import requests
import logging
import shutil
import time
import json

from pathlib import Path
from dateutil import parser
from guessit import guessit
from logging.handlers import TimedRotatingFileHandler

from configs import Movies_path
from configs import TV_path
from configs import sonarr_key
from configs import sonarr_address
from configs import completed_path
from configs import torrents_path

try:
 logging.basicConfig(handlers=[logging.FileHandler("/config/home-assistant.log"),TimedRotatingFileHandler(os.path.dirname(__file__) + "furk.log", when="midnight", interval=1, backupCount=7),logging.StreamHandler()],format='%(asctime)s %(levelname)s (Furk Link-Check) %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
except:
 logging.basicConfig(handlers=[TimedRotatingFileHandler(os.path.dirname(__file__) + "furk.log", when="midnight", interval=1, backupCount=7),logging.StreamHandler()],format='%(asctime)s %(levelname)s (Furk Link-Check) %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')


flagged = {}
removing = []
removed = 0

sonarr_url = sonarr_address + '/api/{}?apikey=' + sonarr_key

#removes any torrents that have not downloaded after one week
logging.info("Checking age of any undownloaded torrents")
current_time = time.time()
for f in os.listdir(torrents_path):
    creation_time = os.path.getctime(torrents_path+"/"+f)
    logging.info(f+" is "+str(int(current_time - creation_time) // (24 * 3600))+" days old")
    if (current_time - creation_time) // (24 * 3600) >= 7:
        logging.info("Deleting "+f+" as it is over a week old")
        os.unlink(torrents_path+"/"+f)

logging.info("Checking integrity of any strm files currently in library")
strmfiles = []
for filename in Path(TV_path).rglob('*.strm'):
    strmfiles.append(filename)
for filename in Path(Movies_path).rglob('*.strm'):
    strmfiles.append(filename)
for filename in strmfiles:
 with open(filename, 'r') as f:
    fileerror = False
    url = f.read()
    f.close()
    try:
     r = requests.head(url)
    except: # file cannot be accessed and furk is not giving an error to say that the file is not found
     try: #check that the furk website is still working
      requests.get("https://www.furk.net/")
     except: # if not then exit
      logging.info("furk.net is not accessible - Exiting....")
      quit()
     finally:
      r.headers = {
      "warning": "file_not_found"
      }
    f = str(filename) 
    try: #checks if furk gives a file not found error
      if r.headers['warning'] == 'file_not_found':
        logging.info("Deleting expired stream" + f.rsplit("/")[-1]) 
        os.remove(filename)
        show = guessit(filename)
        title = show.get('title')
        seasonNumber = show.get('season')
        episodeNumber = show.get('episode')
        series = requests.get(sonarr_url.format('series'))
        series = series.json()
        for x in series:
         if x["title"] == title:
            seriesId = x["id"]
            break
        data = {'name':'rescanSeries','seriesId': seriesId}
        requests.post(sonarr_url.format('command'),json=data)
        episodes = requests.get(sonarr_url.format('episode'), params={'SeriesiD':seriesId})
        episodes = episodes.json()
        for data in episodes:
         if data['seasonNumber'] == seasonNumber and data['episodeNumber'] == episodeNumber:
            data['monitored']=True
            data = str(json.dumps(data))
            break

        requests.put(sonarr_url.format('episode'), data=data, headers = {"Content-Type": "application/json"})
        requests.get(sonarr_url.format('wanted/missing'), data=data, headers = {"Content-Type": "application/json"})  

    except KeyError:
     logging.info("Keeping active stream " + f.rsplit("/")[-1])
 
 
for folder in os.listdir(completed_path):
 elapsed = datetime.datetime.utcnow() - datetime.datetime.utcfromtimestamp(os.path.getmtime(completed_path+"/"+folder))  
 if elapsed > datetime.timedelta(hours=3):
    shutil.rmtree(completed_path+"/"+folder)
