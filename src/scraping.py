#  __    __     _                            _   
# / / /\ \ \___| | ___ ___  _ __ ___   ___  | |_ 
# \ \/  \/ / _ \ |/ __/ _ \| '_ ` _ \ / _ \ | __|
#  \  /\  /  __/ | (_| (_) | | | | | |  __/ | |_ 
#   \/  \/ \___|_|\___\___/|_| |_| |_|\___|  \__|
#                                                 
# Asynchronous File Downloader
# 
# This code was developed by ChatGPT. Including this heading!
# 
# This script downloads files from a website using 
#   asynchronous programming techniques.
#
# Enjoy!


import asyncio
import os
import pickle
import threading
from collections import namedtuple
from urllib.parse import urljoin

import aiohttp
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from .utils import VerilogInstance


base_url = "https://www.synopsys.com/"
url = "https://www.synopsys.com/dw/buildingblock.php"
response = requests.get(url)

soup = BeautifulSoup(response.content, "html.parser")
table = soup.find("table")

# Define a namedtuple to store the link and description
Link = namedtuple("Link", ["url", "description"])

# Create an empty list to store the links
links = []

# Find all rows in the table
rows = table.find_all("tr")

# Loop through each row and extract the href links and descriptions
for row in rows:
    cols = row.find_all("td")
    if cols:
        href = cols[0].find("a")["href"]
        description = cols[1].text.strip()
        full_url = urljoin(base_url, href)
        link = Link(full_url, description)
        links.append(link)

print("Links collect over.")

# Create the "instantiation_demo" folder if it does not exist
if not os.path.exists("instantiation_demo"):
    os.makedirs("instantiation_demo")


# Define an asynchronous function to download a file and return its content
async def download_file(session, url, description: str):
    async with session.get(url) as response:
        code =  await response.read()
        return VerilogInstance(code, description)

# Define an asynchronous function to download all files
async def download_all_files(links):
    async with aiohttp.ClientSession() as session:
        tasks = []
        hrefs = []
        for link in tqdm(links):
            # find the <a> tag element based on the text between the opening and closing <a> tags
            response = await session.get(link.url)
            soup = BeautifulSoup(await response.text(), "html.parser")
            a_tag = soup.find("a", string="Direct Instantiation in Verilog")
            if a_tag is None:
                tqdm.write(f'Warning: "Direct Instantiation in Verilog" not found in {link.url}')
            else:
                # extract the href attribute of the <a> tag
                href = a_tag["href"]
                hrefs.append(href)
                # submit a download task to the event loop
                task = asyncio.ensure_future(download_file(session, href, link.description))
                tasks.append(task)
        # wait for all download tasks to complete
        results = await asyncio.gather(*tasks)
        
        # save the results to a pickle file "scraping_results.pkl"
        with open("scraping_results.pkl", "wb") as f:
            pickle.dump(results, f)

# Create a new event loop in a separate thread and run the download function
def run_download():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(download_all_files(links))

thread = threading.Thread(target=run_download)
thread.start()
thread.join()