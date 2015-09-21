__author__ = "Frederik Lauber"
__copyright__ = "Copyright 2014"
__license__ = "?"
__version__ = "0.2"
__maintainer__ = "Frederik Lauber"
__status__ = "Development"
__contact__ = "https://flambda.de/impressum.html"


import json
import urllib.request

from scon_actions import _uni2bin, _bin2uni, _hash_password, _salted_password, _challenge_response

def response_from_password(password, salt, challenge):
	return _challenge_response(_salted_password(password, salt), challenge)

url = 'https://lablet.vega.uberspace.de/scon/db.cgi'
#url = 'https://lablet.vega.uberspace.de/scon/db_ustest.cgi'
#url = 'https://lablet.vega.uberspace.de/scon/json_bounce.cgi'

def auth_session(session_id, pw, salt, challenge):
	data = {"action": "auth_session", "session_id": session_id, "response": _bin2uni(response_from_password(pw, salt, challenge))}
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
print(tmp)
salt = _uni2bin(tmp["salt"])
challenge = _uni2bin(tmp["challenge"])
session_id = tmp["session_id"]
print("Challenge: " + _bin2uni(challenge))
print("Session_id: " + session_id)
print("Salt: " + _bin2uni(salt))
print("Auth session")
k = auth_session(session_id, "test".encode("utf-8"), salt, challenge)
# should fail
print(k)
print("Projects:")
k = get_projects(session_id)
print(k)
# should show nothing
print("Experiments")
k = get_experiments(session_id)
print(k)
print("No idea")
k = get_last_entry_ids(session_id, k["experiments"][0][1], 20)
print(k)
k = get_entry(session_id, 5)
print(k)



# should work
k = auth_session(session_id, "test".encode("utf-8"), salt, challenge)
print(k)
k = get_projects(session_id)
print(k)
#should show nothing