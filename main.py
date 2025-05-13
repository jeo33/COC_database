#!/usr/bin/env python3
"""
app.py

A simple Flask backend to proxy Clash of Clans API requests.
Receives requests from any machine and returns player JSON.

Usage:
  pip install flask requests
  export COC_API_TOKEN="your_jwt_here"
  python app.py

Then on another PC, request:
  curl "http://<EC2_PUBLIC_IP>:5000/player?tag=%238YCYYQ2R"
"""

import os
import sys
from flask import Flask, jsonify, request
import requests
import urllib.parse
from player import *
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
# Load your API token from environment variable
API_TOKEN = os.getenv("COC_API_TOKEN")
if not API_TOKEN:
    print("Error: Please set the COC_API_TOKEN environment variable.", file=sys.stderr)
    sys.exit(1)

BASE_URL = "https://api.clashofclans.com/v1"

def fetch_player(player_tag: str) -> dict:
    """Fetch data from Clash of Clans API for a given player tag."""
    tag_encoded = urllib.parse.quote(player_tag, safe="")
    url = f"{BASE_URL}/players/{tag_encoded}"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Accept":        "application/json"
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()

@app.route("/player", methods=["GET"])
def player_endpoint():
    """
    Endpoint: /player?tag=#8YCYYQ2R
    Expects `tag` query parameter with the player tag (including the '#').
    """
    tag = request.args.get("tag")
    if not tag:
        return jsonify({"error": "Missing 'tag' query parameter"}), 400
    try:
        data = fetch_player(tag)
    except requests.HTTPError as e:
        return jsonify({"error": str(e), "status_code": e.response.status_code}), e.response.status_code

    return jsonify(data)

if __name__ == "__main__":
    # Listen on all interfaces so remote PCs can connect
    app.run(host="0.0.0.0", port=5000, debug=True)
