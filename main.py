#!/usr/bin/env python3
import os
import sys
import argparse
import requests
import urllib.parse
import json
from player import  *
def fetch_player_info(player_tag: str):
    # Read API token from environment
    api_token = os.environ.get("COC_API_TOKEN")
    if not api_token:
        print("Error: Please set the COC_API_TOKEN environment variable.", file=sys.stderr)
        sys.exit(1)

    # URL-encode the tag (handles leading '#')
    tag_encoded = urllib.parse.quote(player_tag, safe='')
    url = f"https://api.clashofclans.com/v1/players/{tag_encoded}"

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Accept":        "application/json"
    }

    resp = requests.get(url, headers=headers)
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(f"HTTP error {resp.status_code}: {e}", file=sys.stderr)
        sys.exit(resp.status_code)
    data = resp.json()
    # or: data = json.loads(resp.text)

    # Instantiate your Pydantic Player model
    player = Player.parse_obj(data)

    # Now you can access everything as attributes
    print(player.name)  # → MieMie is 4 cat
    print(player.clan.name)  # → 龍盟
    print(len(player.achievements))  # number of achievements
    print([t.name for t in player.troops[:5]])  # first 5 troop names

def main():
    parser = argparse.ArgumentParser(description="Fetch Clash of Clans player info")
    parser.add_argument("player_tag", help="Player tag, e.g. #8YCYYQ2R")
    args = parser.parse_args()

    fetch_player_info(args.player_tag)

if __name__ == "__main__":
    main()
