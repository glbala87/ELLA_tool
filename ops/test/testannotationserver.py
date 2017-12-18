import pytest
from flask import *
import re
import socket
import os
import json

app = Flask(__name__)

JOBSTATUS = ["PENDING", "SUCCESS"]

@app.route('/api/v1/status', defaults={"task_id": None})
@app.route('/api/v1/status/<task_id>')
def taskstatus(task_id):
    if task_id == None:
        return "foo"
    else:
        taskstatus.count += 1
        # Will return PENDING first time, and SUCCESS second time
        return jsonify({
            "active": bool(taskstatus.count % 2),
            "error": False,
        })
taskstatus.count = 0

@app.route('/api/v1/process/<task_id>', methods=["GET", "DELETE"])
def process(task_id):
    return "Dummy data that will fail deposit"

@app.route('/api/v1/annotate', methods=['POST'])
def annotate():
    data = request.get_data()
    return json.dumps({"task_id": "123456789"})

if __name__ == "__main__":
    ANNOTATION_SERVICE = os.environ["ANNOTATION_SERVICE_URL"]
    host = re.findall("//([^:]*)", ANNOTATION_SERVICE)[0]
    assert socket.gethostbyname(host) == socket.gethostbyname("localhost")
    port = int(re.findall(":(\d+)", ANNOTATION_SERVICE)[0])
    app.run(debug=True, host=host, port=port)