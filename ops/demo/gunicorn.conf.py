import multiprocessing

bind = 'unix:/socket/api.sock'
backlog = 1024
workers = 4
daemon = False
loglevel = 'debug'
errorlog = '-'
accesslog = '-'