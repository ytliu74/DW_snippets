import asyncio
import os
import threading
from collections import namedtuple
from urllib.parse import urljoin

import aiohttp
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup

if __name__ == "__main__":

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
    async def download_file(session, url):
        async with session.get(url) as response:
            return await response.read()

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

    # Create a new event loop in a separate thread and run the download function
    def run_download():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(download_all_files(links))

    thread = threading.Thread(target=run_download)
    thread.start()
    thread.join()
