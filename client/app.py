import os
import logging
from flask import Flask, jsonify

# Force create logs directory and set up simple logging
os.makedirs('/app/logs', exist_ok=True)

# SIMPLE LOGGING SETUP
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/app.log', mode='a'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)

# Import routes after setting up logging
from routes.circuitBreaker import circuitBreaker_bp
from routes.retries import retries_bp

app.register_blueprint(circuitBreaker_bp)
app.register_blueprint(retries_bp)

@app.route("/")
def hello():
    logging.info("ROOT ENDPOINT CALLED - This should appear in logs")
    print("PRINT STATEMENT - This should appear in container logs")
    return jsonify({"message": "Hello"}), 200

@app.route("/test")
def test():
    logging.info("TEST ENDPOINT CALLED")
    print("TEST PRINT")
    return jsonify({"test": "logging test"}), 200

if __name__ == "__main__":
    logging.info("=== FLASK APP STARTING ===")
    print("=== FLASK APP STARTING (print) ===")
    app.run(host="0.0.0.0", port=5001, debug=True)