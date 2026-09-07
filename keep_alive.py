from flask import Flask, jsonify, request
from threading import Thread, Lock
import logging
import os

app = Flask(__name__)
logger = logging.getLogger(__name__)

# Mutex to ensure only one web-triggered trading cycle runs concurrently
_scan_lock = Lock()

def _trigger_background_cycle(is_routine: bool = False):
    def worker():
        if not _scan_lock.acquire(blocking=False):
            logger.info("Web-triggered cycle skipped: Another trading cycle is already in progress.")
            return
        try:
            logger.info(f"Web-triggered Trading Cycle started (is_routine={is_routine})...")
            from scheduler import run_trading_cycle
            run_trading_cycle(is_routine=is_routine)
        except Exception as e:
            logger.error(f"Error in web-triggered trading cycle: {e}", exc_info=True)
        finally:
            _scan_lock.release()

    t = Thread(target=worker, daemon=True)
    t.start()

@app.route('/', methods=['GET', 'HEAD', 'POST', 'OPTIONS'])
@app.route('/health', methods=['GET', 'HEAD', 'POST', 'OPTIONS'])
@app.route('/ping', methods=['GET', 'HEAD', 'POST', 'OPTIONS'])
@app.route('/healthz', methods=['GET', 'HEAD', 'POST', 'OPTIONS'])
def home():
    if request.method == 'OPTIONS':
        return '', 204
    if request.headers.get('Accept') == 'application/json' or request.args.get('format') == 'json':
        return jsonify({
            "status": "ok",
            "service": "Gold Trading AI",
            "message": "I'm alive!",
            "patch": "1.7.2"
        }), 200
    return "I'm alive! Gold Trading AI is running (Patch 1.7.2).", 200

@app.route('/cron', methods=['GET', 'HEAD', 'POST', 'OPTIONS'])
@app.route('/cronjob', methods=['GET', 'HEAD', 'POST', 'OPTIONS'])
@app.route('/trigger', methods=['GET', 'HEAD', 'POST', 'OPTIONS'])
@app.route('/scan', methods=['GET', 'HEAD', 'POST', 'OPTIONS'])
@app.route('/run', methods=['GET', 'HEAD', 'POST', 'OPTIONS'])
def trigger_cron():
    """Triggered by external cron services (e.g. cron-job.org) to keep awake and scan market."""
    if request.method == 'OPTIONS':
        return '', 204
    
    # Check if caller wants routine (4h) or sniper (15m) scan
    is_routine = request.args.get('routine', 'false').lower() == 'true'
    _trigger_background_cycle(is_routine=is_routine)
    
    return jsonify({
        "status": "ok",
        "service": "Gold Trading AI",
        "action": "triggered_scan",
        "routine": is_routine,
        "message": "Cronjob received successfully. Market scan initiated in background.",
        "patch": "1.7.2"
    }), 200

@app.route('/check', methods=['GET', 'HEAD', 'POST', 'OPTIONS'])
def web_check():
    """Web endpoint equivalent to Discord #check."""
    if request.method == 'OPTIONS':
        return '', 204
    return jsonify({
        "status": "online",
        "service": "Gold Trading AI",
        "patch": "1.7.2",
        "message": "ระบบ AI พร้อมทำงานปกติครับ"
    }), 200

@app.route('/checkgold', methods=['GET', 'HEAD', 'POST', 'OPTIONS'])
def web_checkgold():
    """Web endpoint equivalent to Discord #checkgold."""
    if request.method == 'OPTIONS':
        return '', 204
    try:
        from indicators import fetch_technical_data, get_spot_gold_price
        spot = get_spot_gold_price()
        snap = fetch_technical_data("15m")
        if snap:
            return jsonify({
                "status": "ok",
                "symbol": "XAUUSD",
                "spot_price": spot or snap.close_price,
                "close_price": snap.close_price,
                "trend": snap.trend_structure,
                "rsi_14": snap.rsi_14,
                "stoch_k": snap.stoch_k,
                "stoch_d": snap.stoch_d,
                "swing_high": snap.swing_high,
                "swing_low": snap.swing_low,
                "patch": "1.7.2"
            }), 200
        return jsonify({"status": "error", "message": "Failed to fetch technical data"}), 502
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

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
