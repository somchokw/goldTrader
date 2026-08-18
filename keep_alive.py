from flask import Flask, jsonify
from threading import Thread
import logging
import os

app = Flask(__name__)

@app.route('/')
@app.route('/health')
@app.route('/ping')
@app.route('/healthz')
def home():
    return "I'm alive! Gold Trading AI is running.", 200

def run():
    # Render binds to 0.0.0.0 and injects PORT env variable (default 10000)
    port = int(os.environ.get("PORT", 10000))
    # Disable flask output to avoid spam
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    # daemon thread will close automatically when the main program exits
    t.daemon = True 
    t.start()

