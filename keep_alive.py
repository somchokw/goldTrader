from flask import Flask, jsonify, request
from threading import Thread
import logging
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'HEAD', 'POST', 'OPTIONS'])
@app.route('/health', methods=['GET', 'HEAD', 'POST', 'OPTIONS'])
@app.route('/ping', methods=['GET', 'HEAD', 'POST', 'OPTIONS'])
@app.route('/healthz', methods=['GET', 'HEAD', 'POST', 'OPTIONS'])
def home():
    if request.headers.get('Accept') == 'application/json':
        return jsonify({
            "status": "ok",
            "service": "Gold Trading AI",
            "message": "I'm alive!"
        }), 200
    return "I'm alive! Gold Trading AI is running.", 200

def run():
    # Render binds to 0.0.0.0 and injects PORT env variable (default 10000)
    port = int(os.environ.get("PORT", 10000))
    # Disable flask output to avoid spam
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=port, threaded=True)

def keep_alive():
    t = Thread(target=run)
    # daemon thread will close automatically when the main program exits
    t.daemon = True 
    t.start()

