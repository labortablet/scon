__author__ = "Frederik Lauber"
__copyright__ = "Copyright 2014"
__license__ = "?"
__version__ = ""
__maintainer__ = "Frederik Lauber"
__status__ = "Development"
__contact__ = "https://flambda.de/impressum.html"


def get_challenge(username):
	return {"status": "success"}


def auth_session(session_id, response):
	return {"status": "success"}


def get_project_ids(session_id):
	return {"status": "success"}


def get_last_entry_ids(session_id, entry_count):
	return {"status": "success"}


def get_entry(session_id, entry_id):
	return {"status": "success"}
