#! /usr/bin/env python3

import os
import logging
from logging.handlers import TimedRotatingFileHandler
import requests
import glob
from guessit import guessit
from configs import furk_api, torrents_path, completed_path, sonarr_key, sonarr_address, radarr_key, radarr_address
from shutil import move

def setup_logging():
    log_format = "%(asctime)s %(levelname)s (Furk-Downloader) %(message)s"
    log_datefmt = "%Y-%m-%d %H:%M:%S"
    handler = TimedRotatingFileHandler("furk.log", when="midnight", backupCount=7)
    formatter = logging.Formatter(log_format, datefmt=log_datefmt)
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger

def scan_directory(directory):
    """
    Scans the specified directory for any .torrent or .magnet files
    Returns a list of the file paths
    """
    torrent_files = glob.glob(os.path.join(directory, "*.torrent"))
    magnet_files = glob.glob(os.path.join(directory, "*.magnet"))
    return torrent_files + magnet_files

def upload_to_furk(api_key, torrent_path):
    # Check if the file is a .torrent or .magnet
    extension = os.path.splitext(torrent_path)[1]

    # Set up API request
    url = f"https://www.furk.net/api/file/add?api_key={api_key}"

    if extension == ".torrent":
        with open(torrent_path, "rb") as f:
            response = requests.post(url, file=f)
    elif extension == ".magnet":
        with open(torrent_path, "r") as f:
            magnet_link = f.read()
            response = requests.post(url, url=magnet_link)
    else:
        raise Exception(f"Invalid file type: {extension}")

    if response.status_code == 200:
        json_response = response.json()
        if json_response["status"] == "ok":
            return [{"url": file["url"], "id": file["id"]} for file in json_response["files"] if file["type"] == "video"]
        else:
            raise Exception(f"Error uploading file: {json_response['error']} - {response.text}")
    else:
        raise Exception(f"Error uploading file: {response.status_code} - {response.text}")

def check_dl_status(api_key, file_ids):
    finished_files = []
    failed_files = []

    for file_id in file_ids:
        url = f"https://www.furk.net/api/file/get?api_key={api_key}&id={file_id}&t_files=1"
        response = requests.get(url)
        
        if response.status_code == 200:
            json_response = response.json()
            if json_response["status"] == "ok":
                dl_status = json_response["files"][0]["dl_status"]
                if dl_status == "finished":
                    finished_files.append(json_response["files"][0]["url_dl"])
                elif dl_status == "failed":
                    failed_files.append(json_response["files"][0]["url_dl"])
            else:
                raise Exception(f"Error uploading file: {json_response['error']} - {response.text}")
        else:
            raise Exception(f"Error getting file details: {response.status_code}")

    return finished_files, failed_files

def generate_strm_files(api_key, video_directory, finished_links):
    strm_files = []

    for link in finished_links:
        # Get the file information
        file_id = link.split("/")[-1]
        url = f"https://www.furk.net/api/file/get?api_key={api_key}&id={file_id}&t_files=1"
        response = requests.get(url)

        if response.status_code == 200:
            json_response = response.json()
            if json_response["status"] == "ok":
                video_files = []
                subtitle_files = []

                # Find video and subtitle files in t_files data
                for file in json_response["files"][0]["t_files"]:
                    if "video" in file["ct"]:
                        video_files.append(file)
                    elif file["ct"] == "text/srt" and file["name"].endswith(".eng.srt"):
                        subtitle_files.append(file)

                # Create .strm files for each video file and download related subtitles
                for video_file in video_files:
                    strm_file_name = os.path.splitext(video_file["name"])[0] + ".strm"
                    strm_file_path = os.path.join(video_directory, strm_file_name)

                    with open(strm_file_path, "w") as strm_file:
                        strm_file.write(video_file["url_dl"])

                    strm_files.append(strm_file_path)

                    # Download and save related subtitle files
                    for subtitle_file in subtitle_files:
                        if os.path.splitext(video_file["name"])[0] == os.path.splitext(subtitle_file["name"])[0].rstrip(".eng"):
                            subtitle_url = subtitle_file["url_dl"]
                            subtitle_file_name = os.path.join(video_directory, subtitle_file["name"])
                            with requests.get(subtitle_url, stream=True) as r:
                                r.raise_for_status()
                                with open(subtitle_file_name, "wb") as f:
                                    for chunk in r.iter_content(chunk_size=8192):
                                        f.write(chunk)
            else:
                raise Exception(f"Error getting file details: {json_response['error']}")
        else:
            raise Exception(f"Error getting file details: {response.status_code}")

    return strm_files

import requests
from guessit import guessit

def update_sonarr(sonarr_key, sonarr_address, strm_files):
    for strm_file in strm_files:
        guess = guessit(strm_file)
        if guess["type"] == "episode":
            # Update Sonarr with the downloaded episode
            sonarr_url = f"{sonarr_address}/api/episode?apikey={sonarr_key}"
            headers = {"Content-Type": "application/json"}

            # Perform a "downloaded episode scan"
            params = {
                "apikey": sonarr_key,
                "path": os.path.dirname(strm_file),
                "downloadClientId": "Furk",
                "importMode": "Move",
            }
            response = requests.post(f"{sonarr_address}/api/command", json=params, headers=headers)

            if response.status_code == 201:
                logging.info(f"Sonarr updated with downloaded episode: {strm_file}")
            else:
                logging.warning(f"Failed to update Sonarr with downloaded episode: {strm_file}")

def update_radarr(radarr_key, radarr_address, strm_files):
    for strm_file in strm_files:
        guess = guessit(strm_file)
        if guess["type"] == "movie":
            # Update Radarr with the downloaded movie
            radarr_url = f"{radarr_address}/api/movie?apikey={radarr_key}"
            headers = {"Content-Type": "application/json"}

            # Perform a "downloaded movie scan"
            params = {
                "apikey": radarr_key,
                "path": os.path.dirname(strm_file),
                "downloadClientId": "Furk",
                "importMode": "Move",
            }
            response = requests.post(f"{radarr_address}/api/command", json=params, headers=headers)

            if response.status_code == 201:
                logging.info(f"Radarr updated with downloaded movie: {strm_file}")
            else:
                logging.warning(f"Failed to update Radarr with downloaded movie: {strm_file}")

def delete_torrent(torrent_path):
    try:
        os.remove(torrent_path)
        logging.info(f"Deleted torrent/magnet file: {torrent_path}")
    except Exception as e:
        logging.error(f"Failed to delete torrent/magnet file: {torrent_path} - {str(e)}")

def main():
    # Set up logging
    logger = setup_logging()

    # Scan the directory for torrent/magnet files
    torrent_files = scan_directory(torrents_path)

    for torrent_file in torrent_files:
        # Upload torrent/magnet file to Furk.net and get direct download URLs
        download_links = upload_to_furk(furk_api, torrent_file)

        # Check the dl_status of each link
        finished_links, failed_links = check_dl_status(furk_api, download_links)

        # Generate .strm files and extract subtitles for finished_links
        strm_files = generate_strm_files(furk_api, finished_links, completed_path)

        for strm_file in strm_files:
            # Move completed strm file to the completed path
            completed_strm_file = os.path.join(completed_path, os.path.basename(strm_file))
            move(strm_file, completed_strm_file)

            # Update Sonarr and Radarr as appropriate
            guess = guessit(os.path.basename(completed_strm_file))
            if "episode" in guess and "season" in guess:
                update_sonarr(sonarr_key, sonarr_address, completed_strm_file)
            elif "movie" in guess:
                update_radarr(radarr_key, radarr_address, completed_strm_file)
            else:
                logger.warning(f"Unrecognized file: {completed_strm_file}")

    # Update Sonarr and Radarr for failed_links
    for failed_link in failed_links:
        guess = guessit(os.path.basename(failed_link))
        if "episode" in guess and "season" in guess:
            update_sonarr(sonarr_key, sonarr_address, failed_link)
        elif "movie" in guess:
            update_radarr(radarr_key, radarr_address, failed_link)
        else:
            logger.warning(f"Unrecognized failed file: {failed_link}")

    # Delete the torrent/magnet file
    delete_torrent(torrent_file)

if __name__ == "__main__":
    main()
