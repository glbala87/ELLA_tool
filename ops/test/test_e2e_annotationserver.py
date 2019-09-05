from flask import Flask, jsonify
import re
import socket
import os

app = Flask(__name__)


@app.route("/api/v1/samples/")
def search_samples():
    return jsonify({"Testsample1": {"test": "test"}})


if __name__ == "__main__":
    ANNOTATION_SERVICE = os.environ["ANNOTATION_SERVICE_URL"]
    host = re.findall("//([^:]*)", ANNOTATION_SERVICE)[0]
    assert socket.gethostbyname(host) == socket.gethostbyname("localhost")
    port = int(re.findall(":(\d+)", ANNOTATION_SERVICE)[0])
    print(host, port)
    app.run(debug=True, host=host, port=port)
