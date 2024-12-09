import json
import requests

def check_status(response):
	if response.status_code >= 400:
		raise Exception(f"API call error: {response.text}")

def get(url, token):
	r = requests.get(url=url, headers={"Authorization": "Bearer {}".format(token)})
	check_status(r)
	return r.json()

def get_all(url, token):
	assert url is not None
	while url is not None:
		obj = get(url, token)
		print(json.dumps(obj, indent=2))
		url = obj["next"]
		yield obj

