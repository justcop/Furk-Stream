#! /usr/bin/env python3

import urllib.request, urllib.error, urllib.parse
import os
import pickle
import datetime
import requests
import logging

from pathlib import Path
from dateutil import parser
from guessit import guessit

from configs import TV_path
from configs import sonarr_key
from configs import sonarr_address

logging.basicConfig(handlers=[logging.FileHandler("/config/home-assistant.log"),logging.StreamHandler()],format='%(asctime)s %(levelname)s (Furk Link-Check) %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

flagged = {}
removing = []
removed = 0

sonarr_url = sonarr_address + '/api/{}?apikey=' + sonarr_key


try:
 oldflagged = pickle.load(open("flagged.pkl", 'rb'))
except:
 pass

try:
    r = urllib.request.urlopen("https://www.furk.net/")
except urllib.error.URLError as e:
    r = e
if r.code in (200, 401):
 for filename in Path(TV_path).rglob('*.strm'):
  with open(filename, 'r') as f:
    url = f.read()
    f.close()
    try:
        r = urllib.request.urlopen(url)
    except urllib.error.URLError as e:
        r = e
    if r.code in (200, 401):
        continue
    else:
        filename = str(filename)
        time = str(datetime.datetime.now())
        try:
         oldtime = oldflagged[filename]['time']
         logging.info("File " + (filename.rsplit("/")[-1]) + " has already been flagged for removal at " + oldtime)
         flagged[filename] = {}
         flagged[filename]['time'] = oldtime
        except:
         logging.info("Flagging " + (filename.rsplit("/")[-1]) + " for removal as stream URL not currently valid. Will check again in 24 hours and remove if still not available")
         flagged[filename] = {}
         flagged[filename]['time'] = time

 for filename in flagged:
    logging.debug("Checking if current file " + (filename.rsplit("/")[-1]) + " has been flagged for more than 24 hours")
    timeflagged = (flagged[filename]['time'])
    logging.info("Flagged at " + timeflagged)
    elapsed = datetime.datetime.now() - parser.parse(timeflagged)
    if elapsed > datetime.timedelta(hours=23):
        removing.append(filename)
        logging.debug("... It Has")
    else:
        logging.debug("... It Hasn't")

 for filename in removing:
    removed +=1
    logging.info("Deleting" + (filename.rsplit("/")[-1]))
    os.remove(filename)
    flagged.pop(filename)
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


 f = open("flagged.pkl","wb")
 pickle.dump(flagged,f)
 f.close()
 
 if removed:   
    logging.info("Removed " + str(removed) + " dead link(s); Sonarr will be alerted and replacements downloaded")
 else:
    logging.info("No persistently dead links found")
    open("test","wb")

else:
    logging.error("Unable to connect to Furk. Is computer connected to internet, or furk down?")
