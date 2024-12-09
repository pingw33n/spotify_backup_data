import common
import csv
import glob
import json
import os
from pathvalidate import sanitize_filename
import requests
import time
import traceback

CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
USER_ID = os.environ["USER_ID"]

FIELDS = ["added_at", "artist", "name", "id", "meta"]

def make_track_entry(track):
    global FIELDS
    added_at = track["added_at"]
    artist = track["track"]["artists"][0]["name"]
    track_name = track["track"]["name"]
    track_id = track["track"]["id"]
    return {
        FIELDS[0]: added_at,
        FIELDS[1]: artist,
        FIELDS[2]: track_name,
        FIELDS[3]: track_id,
        FIELDS[4]: None,
    }

def save_playlist(path, id, name, tracks):
    tracks.sort(key=lambda e: e["added_at"])

    meta = {
        FIELDS[0]: None,
        FIELDS[1]: None,
        FIELDS[2]: None,
        FIELDS[3]: None,
        FIELDS[4]: json.dumps({"id": id, "name": name}),
    }

    print(json.dumps(tracks, indent=2))

    fname_suffix = sanitize_filename(f" {id}.csv")
    for existing in glob.glob(f"{path}/*{fname_suffix}"):
        os.remove(existing)

    path = f"{path}/{sanitize_filename(name)}{fname_suffix}"
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL, fieldnames=FIELDS)
        w.writeheader()
        w.writerow(meta)
        w.writerows(tracks)

def main():
    root_path = os.path.dirname(os.path.realpath(__file__))
    playlists_path = os.path.join(root_path, "data", "playlists")
    print(playlists_path)
    os.makedirs(playlists_path, exist_ok=True)

    r = requests.post("https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(CLIENT_ID, CLIENT_SECRET))
    common.check_status(r)
    token = r.json()["access_token"]

    for playlists in common.get_all("https://api.spotify.com/v1/users/{}/playlists".format(USER_ID), token):
        for pl in playlists["items"]:
            if pl is None or not pl["public"]:
                continue
            pl_name = pl["name"]
            print(pl_name)

            all_tracks = []
            for tracks in common.get_all(pl["href"] + "/tracks?limit=100", token):
                for track in tracks["items"]:
                    all_tracks.append(make_track_entry(track))

            save_playlist(playlists_path, pl["id"], pl_name, all_tracks)

def retry(f, delay_secs = 5, max_delay_secs = 60):
    attempt = 1
    while True:
        try:
            return f()
        except Exception:
            print(f"Error occurred (attempt {attempt}), will retry in {delay_secs} s")
            traceback.print_exc()
            time.sleep(delay_secs)
            delay_secs = min(delay_secs * 2, max_delay_secs)
            attempt += 1

retry(main)