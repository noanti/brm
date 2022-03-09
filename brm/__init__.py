import os
import re
import time

import httpx
import zipfile
import logging
from tqdm import tqdm
from os.path import expanduser
import subprocess

logging.basicConfig(level='INFO')

HOMEPAGE = "https://www.minecraft.net/en-us/download/server/bedrock"
DOWNLOAD_URL_REGEX = re.compile(r"https://minecraft.azureedge.net/bin-linux/bedrock-server-([\d.]+).zip")

HOME = expanduser("~")
MAIN_DIR = os.path.join(HOME, ".brm")
DOWNLOADS_DIR = 'downloads'
SERVER_DIR = 'server'
CONFIG_DIR = 'config'
config_files = ['server.properties', 'allowlist.json', 'permissions.json', 'worlds']


def get_latest_download_url():
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 8_0 like Mac OS X) AppleWebKit/600.1.4 '
                      '(KHTML, like Gecko) Mobile/12A365 MicroMessenger/6.0 NetType/WIFI',
    }
    client = httpx.Client(headers=headers, http2=True)
    r = client.get(HOMEPAGE, timeout=5)
    if r.status_code != 200:
        raise ValueError(r)
    match = DOWNLOAD_URL_REGEX.search(r.text)
    url, version = match.group(0), match.group(1)
    logging.info(f"Latest version: {version}")
    return url, version


def download(url, path):
    logging.info(f'Downloading {url}')
    with open(path, 'wb') as download_file:
        with httpx.stream("GET", url) as response:
            total = int(response.headers["Content-Length"])
            with tqdm(total=total, unit_scale=True, unit_divisor=1024, unit="B") as progress:
                num_bytes_downloaded = response.num_bytes_downloaded
                for chunk in response.iter_bytes():
                    download_file.write(chunk)
                    progress.update(response.num_bytes_downloaded - num_bytes_downloaded)
                    num_bytes_downloaded = response.num_bytes_downloaded


def setup_latest_server():
    url, latest_version = get_latest_download_url()
    local_path = os.path.join(DOWNLOADS_DIR, f'{latest_version}.zip')
    if not os.path.exists(local_path):
        download(url, local_path)

    os.system(f'rm -r {SERVER_DIR}')
    with zipfile.ZipFile(local_path, 'r') as zip_ref:
        zip_ref.extractall(SERVER_DIR)

    for f in config_files:
        if os.path.exists(f'{CONFIG_DIR}/{f}'):
            os.system(f'rm {SERVER_DIR}/{f}')
        else:
            os.system(f'mv {SERVER_DIR}/{f} {CONFIG_DIR}')
        os.system(f'ln -s ../{CONFIG_DIR}/{f} {SERVER_DIR}/{f}')
    os.system('chmod +x ./server/bedrock_server')
    with open('CURRENT_VERSION', 'w') as f:
        f.write(latest_version)


def check_outdated():
    if not os.path.exists('CURRENT_VERSION'):
        return True

    with open('CURRENT_VERSION') as f:
        current_version = f.read()

    url, latest_version = get_latest_download_url()
    return latest_version != current_version


def main():
    os.makedirs(MAIN_DIR, exist_ok=True)
    os.chdir(MAIN_DIR)
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    os.makedirs(SERVER_DIR, exist_ok=True)
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(f'{CONFIG_DIR}/worlds', exist_ok=True)

    if check_outdated():
        logging.info('current version is outdated, updating')
        setup_latest_server()

    server_process = subprocess.Popen(['./bedrock_server'], cwd='server')

    while 1:
        try:
            if check_outdated():
                logging.info('current version is outdated, updating')
                setup_latest_server()
                server_process.kill()
                server_process = subprocess.Popen(['./bedrock_server'], cwd='server')
        except Exception:
            pass

        time.sleep(3600)


if __name__ == '__main__':
    main()



