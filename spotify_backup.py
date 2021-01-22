import csv
import json
import os
import requests

CLIENT_ID = os.environ("CLIENT_ID")
CLIENT_SECRET = os.environ("CLIENT_SECRET")
USER_ID = os.environ("USER_ID")

FIELDS = ["added_at", "artist", "name", "id", "meta"]

root_path = os.path.dirname(os.path.realpath(__file__))
playlists_path = os.path.join(root_path, "playlists")
os.makedirs(playlists_path, exist_ok=True)

r = requests.post("https://accounts.spotify.com/api/token", data={"grant_type": "client_credentials"}, auth=(CLIENT_ID, CLIENT_SECRET)) 
token = json.loads(r.text)["access_token"]

def get(url):
	global token
	r = requests.get(url=url, headers={"Authorization": "Bearer {}".format(token)})
	return json.loads(r.text)	

playlists_url = "https://api.spotify.com/v1/users/{}/playlists".format(USER_ID)
while playlists_url is not None:
	playlists = get(playlists_url)
	for pl in playlists["items"]:
		if pl["owner"]["id"] != USER_ID:
			continue
		pl_name = pl["name"]

		all_tracks = []

		tracks_url = pl["href"] + "/tracks?limit=100"
		while tracks_url is not None:
			tracks = get(tracks_url)
			
			for track in tracks["items"]:
				added_at = track["added_at"]
				artist = track["track"]["artists"][0]["name"]
				track_name = track["track"]["name"]
				track_id = track["track"]["id"]
				all_tracks.append({
					FIELDS[0]: added_at, 
					FIELDS[1]: artist, 
					FIELDS[2]: track_name, 
					FIELDS[3]: track_id,
					FIELDS[4]: None,
				})

			tracks_url = tracks["next"]

		all_tracks.sort(key=lambda e: e["added_at"])

		meta = {
			FIELDS[0]: None, 
			FIELDS[1]: None, 
			FIELDS[2]: None, 
			FIELDS[3]: None,
			FIELDS[4]: json.dumps({"name": pl_name}),
		}

		with open(os.path.join(playlists_path, "{}.csv".format(pl_name)), "w", newline="") as f:
			w = csv.DictWriter(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL, fieldnames=FIELDS)
			w.writeheader()
			w.writerow(meta)
			w.writerows(all_tracks)
	playlists_url = playlists["next"]
