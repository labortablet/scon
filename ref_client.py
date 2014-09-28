__author__ = "Frederik Lauber"
__copyright__ = "Copyright 2014"
__license__ = "?"
__version__ = ""
__maintainer__ = "Frederik Lauber"
__status__ = "Development"
__contact__ = "https://flambda.de/impressum.html"

import json
import hashlib
import urllib.request

import bcrypt
from scon_actions import _uni2bin, _bin2uni


pw_db = "test"
value_db = "$2y$10$wbBPkWPW3dPqgLNR4GlvGeTqf2pWenxSz5pROlX/VMjmz6h1ye/.a"
salt_db = "wbBPkWPW3dPqgLNR4GlvGg"

url = 'https://lablet.vega.uberspace.de/scon/db.cgi'
#url = 'https://lablet.vega.uberspace.de/scon/db_ustest.cgi'
#url = 'https://lablet.vega.uberspace.de/scon/json_bounce.cgi'

def auth_session(session_id, pw, salt, challenge):
	salt = bcrypt.gensalt(10, _uni2bin(salt))  # modified the bcrypt file to allow my own random bytes
	challenge = bcrypt.gensalt(10, _uni2bin(challenge))  #modified the bcrypt file to allow my own random bytes
	hash_pw = hashlib.sha256(pw).digest()
	salted_pw = bcrypt.hashpw(hash_pw, salt)
	response = bcrypt.hashpw(salted_pw, challenge)
	data = {"action": "auth_session", "session_id": session_id, "response": _bin2uni(response)}
	return _prepare_data_and_response(data)

def get_last_entry_ids(session_id, entry_count):
	return {"status": "success"}


def get_entry(session_id, entry_id):
	data = {"action": "get_entry", "session_id": session_id, "entry_id": entry_id}
	return _prepare_data_and_response(data)


def _prepare_data_and_response(data):
	headers = dict()
	headers['Content-Type'] = 'application/json;charset=utf-8'
	json_data = json.dumps(data)
	post_data = json_data.encode('utf-8')
	req = urllib.request.Request(url, post_data, headers)
	response = urllib.request.urlopen(req)
	response_read_and_decoded = response.read().decode("utf8")
	return json.loads(response_read_and_decoded)


def get_challenge(username):
	data = {"action": "get_challenge", "username": username}
	return _prepare_data_and_response(data)


def get_version():
	data = {"action": "version"}
	return _prepare_data_and_response(data)

def get_projects(session_id):
	data = {"action": "get_projects", "session_id": session_id}
	return _prepare_data_and_response(data)


def get_experiments(session_id):
	data = {"action": "get_experiments", "session_id": session_id}
	return _prepare_data_and_response(data)


def get_last_entry_ids(session_id, experiment_id, entry_count):
	data = {"action": "get_last_entry_ids", "experiment_id": experiment_id, "session_id": session_id,
	        "entry_count": entry_count}
	return _prepare_data_and_response(data)


print("Version:")
print(get_version())
tmp = get_challenge("fredi@uni-siegen.de")
print("Challenge:")
salt = tmp["salt"]
challenge = tmp["challenge"]
session_id = tmp["session_id"]
print("Challenge: " + challenge)
print("Session_id: " + session_id)
print(salt)
print(salt_db)
print("Auth session")
k = auth_session(session_id, pw_db.encode("utf-8"), salt, challenge)
print(_uni2bin(k["a"]))
# projects = get_projects(session_id)
#print("Projects:")
#print(projects)
#experiments = get_experiments(session_id)
#print("Experiments")
#print(experiments)
#experiments = experiments["experiments"]
#experiment = experiments[0]
#print("Hallo")
#print(experiment)
#k = get_last_entry_ids(session_id, experiment[0], 20)
#k = k["entry_ids"]
#print(k)
#print(get_entry(session_id, k[0]))