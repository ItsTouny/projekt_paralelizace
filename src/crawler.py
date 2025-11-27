"""
Author: Tony Menšík
Project: Parallel Web Crawler
Description: This crawler downloads content from web pages (title and meta description)
             and saves the results to a CSV file. It uses multithreading for parallel
             downloads. The URL queue is thread-safe (queue.Queue), and CSV writes are
             protected by a Lock to prevent conflicts.
"""
import json
import os
import threading
import queue
import requests
from bs4 import BeautifulSoup
import csv


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
output_file = os.path.join(PROJECT_ROOT, "results.csv")
CONFIG_FILE = os.path.join(PROJECT_ROOT+"/config", "config.json")

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = json.load(f)

if os.path.exists(output_file):
    os.remove(output_file)

url_queue = queue.Queue()

output_file = "results.csv"
lock = threading.Lock()

base_domains = config["base_domains"]
paths = config["paths"]
urls = []

for domain in base_domains:
    for path in paths:
        urls.append(domain + path)

for url in urls:
    url_queue.put(url)

def crawl_worker():
    """
       Function representing a single crawler thread.
       Takes URLs from the queue, downloads the page content,
       and writes the results to a CSV file.

       Synchronization:
           - URL queue is thread-safe, so get() is safe for multiple threads.
           - CSV writing is protected by a Lock to prevent race conditions.
       """
    while not url_queue.empty():
        url = url_queue.get()
        try:
            response = requests.get(url, timeout=5)
            soup = BeautifulSoup(response.text, "html.parser")
            title = "No title"
            if soup.title:
                title = soup.title.string
            description_tag = soup.find("meta", {"name": "description"})
            description = "No description"
            if description_tag and description_tag["content"] != "":
                description = description_tag["content"]

            with lock:
                with open(output_file, "a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([url, title, description])
            print(f"Crawled: {url}")
        except Exception as e:
            print(f"Error crawling {url}: {e}")
        finally:
            url_queue.task_done()

num_threads = 5
threads = []

for x in range(num_threads):
    t = threading.Thread(target=crawl_worker)
    t.start()
    threads.append(t)

url_queue.join()

for t in threads:
    t.join()

print("Crawling finished.")
