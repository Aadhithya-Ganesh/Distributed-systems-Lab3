from flask import Flask, jsonify
from random import randint

app = Flask(__name__)

@app.route("/circuit", methods=["GET"])
def circuit():
    n = randint(0, 10)
    if n in [5, 6, 7, 8, 9]:
        return jsonify({"message" : "Failed"}), 500 
    return jsonify({"message" : "Hello"}), 200

@app.route("/retries", methods=["GET"])
def retries():
    n = randint(0, 10)
    if n in [4, 5, 6, 7, 8, 9]:
        return jsonify({"message" : "Failed"}), 500 
    return jsonify({"message" : "Hello"}), 200

@app.route("/chaos", methods=["GET"])
def chaos():
    print("HERE")
    return jsonify({"message" : "Hello"}), 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)