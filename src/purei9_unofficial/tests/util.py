import os
import json

def load_secrets():
	filename = os.getenv("HOME") + "/.config/purei9_unofficial/test_secrets.json"
	try:
		with open(filename, "r") as fp:
			return json.loads(fp.read())
	except:
		raise Exception("Could not load tests secrets from " + filename)
