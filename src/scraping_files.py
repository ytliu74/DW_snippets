#  __    __     _                            _   
# / / /\ \ \___| | ___ ___  _ __ ___   ___  | |_ 
# \ \/  \/ / _ \ |/ __/ _ \| '_ ` _ \ / _ \ | __|
#  \  /\  /  __/ | (_| (_) | | | | | |  __/ | |_ 
#   \/  \/ \___|_|\___\___/|_| |_| |_|\___|  \__|
#                                                 
# Asynchronous Parallel File Downloader
# 
# This code was developed by ChatGPT. Including this heading!
# 
# This script downloads files from a website using 
#   asynchronous programming and parallel processing techniques.
#
# Enjoy!


import math
import threading

import aiohttp
import asyncio
import os
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from urllib.parse import urljoin
from collections import namedtuple

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

print("Links collected.")

# Create the "instantiation_demo" folder if it does not exist
if not os.path.exists("instantiation_demo"):
    os.makedirs("instantiation_demo")


# Define an asynchronous function to download a file and return its content
async def download_file(session, url):
    async with session.get(url) as response:
        return await response.read()


# Define an asynchronous function to download a subset of files
async def download_subset(links_subset):
    async with aiohttp.ClientSession() as session:
        tasks = []
        hrefs = []
        for link in links_subset:
            # find the <a> tag element based on the text between the opening and closing <a> tags
            response = await session.get(link.url)
            soup = BeautifulSoup(await response.text(), "html.parser")
            table = soup.find("table")
            a_tag = table.find("a", string="Direct Instantiation in Verilog")
            if a_tag is None:
                tqdm.write(f'Warning: "Direct Instantiation in Verilog" not found in {link.url}')
            else:
                # extract the href attribute of the <a> tag
                href = a_tag["href"]
                hrefs.append(href)
                # submit a download task to the event loop
                task = asyncio.ensure_future(download_file(session, href))
                tasks.append(task)
        # wait for all download tasks to complete
        results = await asyncio.gather(*tasks)
        # save the content of each file to a separate file
        for i, result in enumerate(results):
            file_name = os.path.basename(hrefs[i])
            file_path = os.path.join("instantiation_demo", file_name)
            with open(file_path, "wb") as f:
                f.write(result)


# Define a function to divide the links into equal subsets
def divide_links(links, num_subsets):
    subset_size = math.ceil(len(links) / num_subsets)
    return [links[i:i+subset_size] for i in range(0, len(links), subset_size)]


# Create a new event loop in a separate thread and run the download function for each subset of links
def run_download(links_subset):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(download_subset(links_subset))


# Divide the links into 8 subsets and assign each subset to a separate thread
links_subsets = divide_links(links, 8)
threads = []
for links_subset in links_subsets:
    thread = threading.Thread(target=run_download, args=(links_subset,))
    thread.start()
    threads.append(thread)

# Wait for all threads to complete
for thread in threads:
    thread.join()