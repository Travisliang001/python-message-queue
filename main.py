from worker import Celery
from worker import fetch_url

# 添加任务到队列
fetch_url.apply_async(args=["https://jsonplaceholder.typicode.com/posts/1"])
fetch_url.apply_async(args=["https://jsonplaceholder.typicode.com/posts/2"])
fetch_url.apply_async(args=["https://jsonplaceholder.typicode.com/posts/3"])