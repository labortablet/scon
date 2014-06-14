#!/usr/bin/env python3
__author__ = "Frederik Lauber"
__copyright__ = "Copyright 2014"
__license__ = "?"
__version__ = ""
__maintainer__ = "Frederik Lauber"
__status__ = "Development"
__contact__ = "https://flambda.de/impressum.html"

#action <= (get_challenge | auth_session | get_project_ids | get_last_entry_ids | get_entry)
#status <= (success | failed)

#status, challenge, session_id <= get_challenge(username)
#status <= auth_session(session_id, response)
#status, [(project_id, project_name) ...] <= get_project_ids(session_id)
#status, [entry_id ...] <= get_last_entry_ids(session_id, project_id)
#status, entry_data <= get_entry(session_id, entry_id)

import sys
import json
import scon_actions
import cgitb
cgitb.enable()

#get json from stdin
try:
	input_json = json.loads(sys.stdin.buffer.read().decode('utf-8'))
except Exception:
	print("Content-Type: text/html\n\n")
	print("<html><body><p>No valid JSON found</p></body></html>")
	sys.exit()

#separate action and arguments
try:
	action = input_json["action"]
	arguments = input_json
	del arguments["action"]
except Exception:
	print("Content-Type: text/html\n\n")
	print("<html><body><p>JSON found, but invalid values</p></body></html>")
	sys.exit()

#execute action
try:
	response_dict = getattr(scon_actions, action)(**arguments)
except Exception as E:
	print("Content-Type: text/html\n\n")
	print("<html><body><p>Exception happened!</p><p>{0}</p></body></html>".format(E))
	sys.exit()

sys.stdout.buffer.write('Content-Type: application/json\n\n'.encode('utf-8'))
sys.stdout.buffer.write(json.dumps(response_dict).encode('utf-8'))
