import os
import multiprocessing

bind = 'unix:/socket/api.sock'
backlog = 1024
workers = int(os.environ.get('NUM_WORKERS', multiprocessing.cpu_count() * 2 + 1))
daemon = False
loglevel = 'debug'
errorlog = '-'
accesslog = '-'
limit_request_line = 8190
