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
import pymysql
import re
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


def get_db():
    return pymysql.connect(
        host='localhost', user='root', password='n3u8c5t9A!',
        database='coc', charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor
    )

def insert_or_update_user_stats(user_tag, stats_dict,
                                host='localhost', user='root',
                                password='n3u8c5t9A!', db='coc'):
    """
    Insert a new row into user_stats or update existing one if user_tag already exists.

    :param user_tag: str, primary key (e.g. "#8YCYYQ2R")
    :param stats_dict: dict, column names → integer values
    """
    # 1) Connect
    conn = pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=db,
        charset='utf8mb4'
    )
    cursor = conn.cursor()

    # 2) Build the INSERT part
    columns = ', '.join(stats_dict.keys())
    placeholders = ', '.join(['%s'] * len(stats_dict))
    # 3) Build the UPDATE part
    update_clause = ', '.join(f"{col}=VALUES({col})" for col in stats_dict.keys())

    sql = (
        f"INSERT INTO user_stats (user_tag, {columns}) "
        f"VALUES (%s, {placeholders}) "
        f"ON DUPLICATE KEY UPDATE {update_clause}"
    )
    data = [user_tag] + list(stats_dict.values())

    # 4) Execute & commit
    cursor.execute(sql, data)
    conn.commit()

    # 5) Clean up
    cursor.close()
    conn.close()
def to_snake(s: str) -> str:
    # lower-case, replace non-alphanum with underscore, strip extras
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', '_', s)
    return s.strip('_')


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


@app.route('/login', methods=['POST'])
@app.route('/login', methods=['POST'])
def login():
    payload = request.get_json()
    username = payload.get('email')      # this is your “username” column
    password = payload.get('password')

    if not username or not password:
        return jsonify({'message': 'Missing username or password'}), 400

    try:
        conn = get_db()
        with conn.cursor() as cur:
            # look up the user by both username and password
            cur.execute("""
                SELECT username, tag, password
                  FROM user
                 WHERE username = %s
                   AND password = %s
                """,
                (username, int(password))
            )
            row = cur.fetchone()

            if not row:
                # no matching user/password pair
                return jsonify({'message': 'Invalid credentials'}), 401

            # found a match — return the full record
            return jsonify(row), 200

    finally:
        conn.close()

@app.route('/register', methods=['POST'])
def register():
    payload = request.get_json()
    username = payload.get('email')   # or payload['username']
    password = payload.get('password')
    tag = payload.get('name')
    if not username or not password:
        return jsonify({'message': 'Missing username or password'}), 400

    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Check if user exists
            cur.execute("SELECT 1 FROM user WHERE username=%s", (username,))
            if cur.fetchone():
                return jsonify({'message': 'User already exists'}), 409

            # Insert new user
            cur.execute(
                "INSERT INTO user (username,tag, password) VALUES (%s,%s, %s)",
                (username, tag,int(password))
            )
            conn.commit()
            return jsonify({'message': 'Registration successful'}), 201
    finally:
        conn.close()










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

    combined = {
        to_snake(item['name']): item['level']
        for key in ('heroes', 'spells','troops',)
        for item in data.get(key, [])
    }
    combined['town_hall_level']=data['townHallLevel']

    insert_or_update_user_stats(data['tag'], combined)
    return jsonify(data)

if __name__ == "__main__":
    # Listen on all interfaces so remote PCs can connect
    app.run(host="0.0.0.0", port=5000, debug=True)
