#! /usr/bin/env python3

import os
import requests
import logging
from guessit import guessit
from urllib.parse import unquote
from configs import furk_api, torrents_path, completed_path, sonarr_key, sonarr_address, radarr_key, radarr_address
from logging.handlers import TimedRotatingFileHandler

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


def download_files():
    processed_files = {}
    for filename in os.listdir(torrents_path):
        if filename.endswith(".torrent") or filename.endswith(".magnet"):
            file_path = os.path.join(torrents_path, filename)
            with open(file_path, "rb") as file:
                if filename.endswith(".torrent"):
                    response = requests.post(
                        "https://www.furk.net/api/dl/add",
                        headers={"Accept": "application/json"},
                        params={"api_key": furk_api},
                        files={"torrent": file},
                    )
                else:  # filename ends with ".magnet"
                    magnet_link = file.read().decode("utf-8")
                    response = requests.post(
                        "https://www.furk.net/api/dl/add",
                        headers={"Accept": "application/json"},
                        params={"api_key": furk_api, "url": magnet_link},
                    )

            if response.status_code != 200:
                print(f"Error uploading {filename}: {response.text}")
            else:
                print(f"Successfully uploaded {filename}")
                processed_files[filename] = []

    return processed_files

def get_video_urls():
    """
    Uses the Furk API to get the direct download URLs of each video file in the Furk download
    and returns a list of the URLs.
    """
    video_urls = []
    response = requests.get(
        "https://www.furk.net/api/dl/get",
        headers={"Accept": "application/json"},
        params={"api_key": furk_api},
    )

    if response.status_code != 200:
        print(f"Error fetching downloads: {response.text}")
        return video_urls

    downloads = response.json().get("downloads", {})
    if not downloads:
        print(response.json())
        return video_urls

    for download in downloads:
        if download["status"] == "active":
            for file in download["files"]:
                if file["content_type"].startswith("video"):
                    video_url = f"https://www.furk.net/ftv/{file['url_dl']}"
                    video_urls.append(video_url)

    return video_urls


def update_sonarr(video_path):
    """
    Updates Sonarr with the downloaded episode and performs a "downloaded episode scan"
    if a TV show is detected in the downloaded video file name.

    Parameters:
    video_path (str): The path to the downloaded video file

    Returns:
    None
    """
    filename = os.path.basename(video_path)
    metadata = guessit(filename)

    if metadata.get("type") == "episode":
        data = {"name": "DownloadedEpisodesScan", "path": video_path}
        response = requests.post(sonarr_url.format("command"), json=data).json()

        if response.get("body") and response["body"].get("completionMessage"):
            print(f"Sonarr update: {response['body']['completionMessage']}")
        else:
            print("Unable to update Sonarr.")
    else:
        print("Not an episode. Skipped updating Sonarr.")

def update_radarr(video_path):
    """
    Updates Radarr with the downloaded movie and performs a "downloaded movie scan"
    if a movie is detected in the downloaded video file name.

    Parameters:
    video_path (str): The path to the downloaded video file

    Returns:
    None
    """
    filename = os.path.basename(video_path)
    metadata = guessit(filename)

    if metadata.get("type") == "movie":
        data = {"name": "DownloadedMoviesScan", "path": video_path}
        response = requests.post(radarr_url.format("command"), json=data).json()

        if response.get("body") and response["body"].get("completionMessage"):
            print(f"Radarr update: {response['body']['completionMessage']}")
        else:
            print("Unable to update Radarr.")
    else:
        print("Not a movie. Skipped updating Radarr.")

def delete_files(magnet_or_torrent_file):
    """
    Deletes the corresponding magnet or torrent file on successfully downloading the .strm file.

    Parameters:
    magnet_or_torrent_file (str): The path to the magnet or torrent file to be deleted

    Returns:
    None
    """
    if os.path.exists(magnet_or_torrent_file):
        try:
            os.remove(magnet_or_torrent_file)
            print(f"Deleted: {magnet_or_torrent_file}")
        except OSError as e:
            print(f"Error deleting file {magnet_or_torrent_file}: {e}")
    else:
        print(f"File not found: {magnet_or_torrent_file}")

def main():
    processed_files = download_files()
    video_urls = get_video_urls()
    saved_strm_files = save_strm_files(video_urls, processed_files)

    for video_url in video_urls:
        video_path = os.path.join(completed_path, unquote(video_url.split("/")[-1]))
        update_sonarr(video_path)
        update_radarr(video_path)

    for magnet_or_torrent_file, strm_files in processed_files.items():
        if strm_files:
            delete_files(magnet_or_torrent_file)

if __name__ == "__main__":
    main()


