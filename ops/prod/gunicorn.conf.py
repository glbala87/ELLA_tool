import multiprocessing

bind = 'unix:/socket/api.sock'
backlog = 1024
workers = multiprocessing.cpu_count() * 2 + 1
daemon = False
loglevel = 'debug'
errorlog = '/logs/api.error.log'
accesslog = '/logs/api.access.log'
