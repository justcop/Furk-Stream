# Convert-torrent-to-.strm-using-Furk.net

My first python script so please be kind.

This script is written to allow the use of the online seedbox website www.furk.net as the main downloader and hoster of media files for use with a home media centre such as Kodi, Emby or Jellyfin etc.

It is currently only fully functional for TV episodes but I intend to add movies in the future.

The script is written with intention of using Sonarr, to monitor and download relevant .torrent file and .magnet files of monitored TV shows. The script, will then work with the 'torrent black hole' feature in Sonarr, request the files to be downloaded in furk and when ready will find the URL at which they are hosted and put this in a .strm file in your TV folder. Strm files can be read by Kodi, Emby or Jellyfin (but not Plex!) and mean that downloaded files do not need to sit on any local storage media.

A second script, 'linker.py' will check that all the strm still contain valid URLs. If the URL is cannot be found on furk for over 24 hours, then it will delete the strm file and signal to sonarr to redownload the episode.


<b>How it works:</b>

1. Checks torrent folder for any .torrent files and turns them in to .magnet files (ie text files containing the magnet url)
2. Goes through each .magnet link one at a time and adds to furk
3. Checks if file is immediately available
4. If so it will grab the data for the playlist file, containing the URLs to all the video files
5. The playlist file will be parsed and each URL outputed as the entry to a .strm file, named as per the show title, season and episode number
6. After each torrent has been processed, Sonarr will be alerted to check for the presence of new episodes and the original .magnet file deleted
7. The process repeats for the next .magnet file
8. If any episode was not available download in step 4 the script will run again after 10 minutes to recheck for this. This will be repeated up to 6 times (ie one hour) before timing out with the next check only happening when the script is rerun via cron (eg after 6 hours)

9. The linker script, will run every 24 hours and check for the integrity of the URLs within any exisiting .strm files.
10. Checking www.furk.net can be resolved (to avoid internet or website being down)
11. Checks each strm file in turn and ensures URL is active
12. Any newly inactive links are flagged for removal with a specific time stamp
13. If the link is already flagged and has been for 23 hours or more, the strm link is deleted [and Sonarr is notified to monitor for the episode again and search for all monitored episodes - **nb the bracketed off part of this feature isn't quite functional yet]

<b>Setup:</b>

1. Setup should be relatively straight forward. rename the 'configs.py - template' to 'configs.py' and fill in to include your furk and sonarr api keys, together with you torrents folder , set as your torrent black hole in sonarr, your completed downloads folder that sonarr monitors for files and your TV folder, where sonarr keeps and organises downloaded files.

2. You should then setup a cronjob to run furk.py say every 6 hours and linker.py to run say every 24 hours, probably in the middle of the night, as per your preferences.

3. The script has the following dependencies which should be download with pip if needed

urllib.request, urllib.error, urllib.parse
os
pickle
datetime
requests
logging
os
glob
requests
json
ast
logging
urllib
time
guessit
bs4
torrentool.api

Within sonarr, make sure to keep, 'monitor deleted episodes' unchecked and feel free to use indexers which can only download magnet links and full season torrents.

<b>Caution:</b>

Furk.net has safeguards to avoid you downloading too much within the cloud, without viewing it. Be careful to avoid reaching these thresholds by keeping lots of media in your cloud library, especially if you let it reload every few months as links begin to fail.


EDIT

This is now setup to work with movies using radarr too. 
