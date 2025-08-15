"""
Minimal MCP Memory Server (Python Flask)
--------------------------------------
Implements /put, /get, /delete endpoints for use with MCPMemoryClient.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

memory = {}

@app.route("/put", methods=["POST"])
  
def put():
    data = request.get_json()
    key = data.get("key")
    value = data.get("value")
    if key is not None:
        memory[key] = value
        return jsonify({"status": "ok"})
    return jsonify({"status": "error", "reason": "No key provided"}), 400

@app.route("/get", methods=["GET"])
  
def get():
    key = request.args.get("key")
    value = memory.get(key)
    return jsonify({"value": value})

@app.route("/delete", methods=["POST"])
  
def delete():
    data = request.get_json()
    key = data.get("key")
    if key in memory:
        del memory[key]
        return jsonify({"status": "ok"})
    return jsonify({"status": "error", "reason": "Key not found"}), 404

  
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
