from flask import Flask
from threading import Thread
import logging

app = Flask('')

@app.route('/')
def home():
    return "I'm alive! Gold Trading AI is running."

def run():
    # Render requires binding to 0.0.0.0 and defaults to port 10000, but they read from PORT env var.
    import os
    port = int(os.environ.get("PORT", 8080))
    # Disable flask output to avoid spam
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    # daemon thread will close automatically when the main program exits
    t.daemon = True 
    t.start()
