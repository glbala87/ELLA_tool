import multiprocessing
import os

bind = "0.0.0.0:8000"
backlog = 1024
workers = int(os.getenv("NUM_WORKERS", multiprocessing.cpu_count() * 2 + 1))
daemon = False
loglevel = "debug"
errorlog = "-"
accesslog = "-"
limit_request_line = 0
timeout = int(os.getenv("GUNICORN_TIMEOUT", 500))
reload = os.getenv("DEVELOP", "").lower() == "true"
