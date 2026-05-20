import webview
import threading
import os
import sys
import time
from flask import send_from_directory

sys.path.insert(0, os.path.dirname(__file__))
from tracker import app

DIST_FOLDER = r"C:\OutreachOS\frontend\dist"

@app.route("/")
def index():
    return send_from_directory(DIST_FOLDER, "index.html")

@app.route("/assets/<path:filename>")
def assets(filename):
    return send_from_directory(os.path.join(DIST_FOLDER, "assets"), filename)

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(DIST_FOLDER, filename)

def run_flask():
    app.run(port=5050, debug=False, use_reloader=False)

if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    time.sleep(1.5)
    webview.create_window(
        title="OutreachOS",
        url="http://localhost:5050",
        width=1280,
        height=800,
        resizable=True,
    )
    webview.start()