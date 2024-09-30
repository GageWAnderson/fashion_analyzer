import time
import schedule
import requests
from chromadb import Client, Settings

def crawl():
    # Your crawling logic here
    print("Crawling websites...")
    # Example: Fetch a website
    response = requests.get("https://example.com")
    # Process the response...

    # Store data in Chroma
    chroma_client = Client(Settings(
        chroma_api_impl="rest",
        chroma_server_host=os.environ.get("CHROMA_HOST", "localhost"),
        chroma_server_http_port=os.environ.get("CHROMA_PORT", "8000")
    ))
    # Use chroma_client to store your crawled data...

def run_crawler():
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    run_crawler()