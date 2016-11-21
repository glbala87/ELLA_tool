from flask import Flask
from werkzeug.routing import BaseConverter
from werkzeug.serving import is_running_from_reloader

from vardb.datamodel import DB
from rest_query import RestQuery

import threading
import atexit
import time
import json

def create_app():
    app = Flask(__name__)

    pollAnnotationServiceThread = threading.Thread()

    def polling(app, event):
        while not event.is_set():
            with app.test_client() as c:
                # Get status of all submitted tasks
                response = c.get("/api/v1/analyses/imports/")
                if response.status_code == 200:
                    status = json.loads(response.get_data())
                    for id in status:
                        # Try to deposit annotated vcf, if successful
                        if status[id] == "SUCCESS":
                            MAX_TRIES = 3
                            WAIT = 5
                            try_no = 0
                            while True:
                                try_no += 1
                                try:
                                    process = c.post("/api/v1/analyses/imports/%s" %id)
                                    break
                                except:
                                    time.sleep(WAIT)
                                    if try_no >= MAX_TRIES:
                                        break
                            c.delete("/api/v1/analyses/imports/%s" % id)
            time.sleep(5)
        print "Received exit signal"

    def startPolling(app):
        global pollAnnotationServiceThread
        # Create event for cancelling thread
        event = threading.Event()
        pollAnnotationServiceThread = threading.Thread(target=polling, args=(app,event))
        pollAnnotationServiceThread.start()

        return event.set

    # Initiate
    if not is_running_from_reloader():
        cancel = startPolling(app)
        atexit.register(cancel)
    return app

# Setup app, and create polling thread
app = create_app()

class ListConverter(BaseConverter):
    def to_python(self, value):
        return value.split(',')

    def to_url(self, values):
        return ','.join(BaseConverter.to_url(value)
                        for value in values)

app.url_map.converters['list'] = ListConverter

db = DB()
engine_kwargs = {
    "pool_size": 5,
    "max_overflow": 10,
    "pool_timeout": 30
}
db.connect(engine_kwargs=engine_kwargs, query_cls=RestQuery)


class ApiError(RuntimeError):
    pass
