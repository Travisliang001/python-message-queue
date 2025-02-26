from celery import Celery
import requests

app = Celery('http_requests', broker='redis://:123456@localhost:6379/0')

@app.task
def fetch_url(url):
    try:
        response = requests.get(url)
        print(f"Response status for {url}: {response.text}")
    except Exception as e:
        print(f"Request failed for {url}: {e}")
