#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "Frederik Lauber"
__copyright__ = "Copyright 2014"
__license__ = "?"
__version__ = ""
__maintainer__ = "Frederik Lauber"
__status__ = "Development"
__contact__ = "https://flambda.de/impressum.html"

import uuid
import configparser
import hashlib
import base64
import cgitb

import pymysql


cgitb.enable()

SERVER_STABLE_RANDOM = u"sadsdasdassadsd"


class LabletBaseException(Exception):
	pass


#encode and decode a binary as a abs64 encoded string
#will return a unicode object so we are independent from transmission encoding
def _uni2bin(uni):
	return base64.b64decode(uni.encode("ascii"))


def _bin2uni(bin):
	return base64.b64encode(bin).decode("ascii")


_config = configparser.ConfigParser()
_config.read_file(open("/home/lablet/.my.cnf"))

_database = pymysql.connect(unix_socket=_config.get('client', 'socket'),
                            port=_config.get('client', 'port'),
                            user=_config.get('client', 'user'),
                            passwd=_config.get('client', 'password'),
                            db="lablet_tabletprojectdb",
                            charset='utf8')

del _config
_cursor = _database.cursor()


def _get_userid_and_salt(username):
	_cursor.execute("""SELECT user_id, password FROM `user` WHERE user_email = %s""", username)
	user_list = _cursor.fetchall()
	#FIXME salt in database is not of binary type yet
	if len(user_list) == 1:
		user_id = user_list[0][0]
		salt = user_list[0][1]
		m = hashlib.md5()
		m.update(salt.encode("utf-8"))
		salt = m.digest()
		return (user_id, salt)
	else:
		m = hashlib.md5()
		m.update(username.encode("utf-8"))
		m.update(SERVER_STABLE_RANDOM.encode("utf-8"))
		salt = m.digest()
		return ("null", salt)

def test(**kwargs):
	return kwargs


def get_challenge(username):
	session_id = uuid.uuid4().bytes
	challenge = uuid.uuid4().bytes
	(user_id, salt) = _get_userid_and_salt(username)
	#FIXME
	#right now all sessions are authorized!!!!!
	#I cannot implement authorisation as the database is still missing the needed fields
	try:
		_cursor.execute("""INSERT INTO user_session (session_id, user_id, session_challenge, authorized) VALUES (%s,%s,%s, True)""",
		                (session_id, user_id, challenge))
	except Exception:
		return {"status": "failed"}
	return {"status": "success",
	        "session_id": _bin2uni(session_id),
	        "salt": _bin2uni(salt),
	        "challenge": _bin2uni(challenge)}


def auth_session(session_id, response):
	#FIXME not yet implemented as database is not far enought yet
	return {"status": "success"}


def get_projects(session_id):
	session_id = uuid.UUID(bytes=_uni2bin(session_id))
	#FIXME we most likely want to use a view here.
	_cursor.execute("""SELECT projects.project_id, projects.project_name, projects.project_description
	FROM `projects`
	INNER JOIN `project_group`
	ON project_group.project_id = projects.project_id
	INNER JOIN `user_group`
	ON user_group.group_id = project_group.group_id
	INNER JOIN `user`
	ON user_group.user_id = user.user_id
	INNER JOIN `user_session`
	ON user_session.user_id = user.user_id
	WHERE user_session.authorized = True AND user_session.session_id = %s""", session_id.bytes)
	projects = _cursor.fetchall()
	return {"status": "success", "projects": projects}


def get_experiments(session_id):
	session_id = uuid.UUID(bytes=_uni2bin(session_id))
	#FIXME we most likely want to use a view here.
	#FIXME added a tippo as the database still has it...
	_cursor.execute("""SELECT project.project_id, experiments.expr_id, experiments.expr_name, experiments.expr_describtion
	FROM `experiments`
	INNER JOIN `projects`
	ON projects.project_id = experiments.project_id
	INNER JOIN `project_group`
	ON project_group.project_id = projects.project_id
	INNER JOIN `user_group`
	ON user_group.group_id = project_group.group_id
	INNER JOIN `user`
	ON user_group.user_id = user.user_id
	INNER JOIN `user_session`
	ON user_session.user_id = user.user_id
	WHERE user_session.authorized = True AND user_session.session_id = %s""", session_id.bytes)
	experiments = _cursor.fetchall()
	return {"status": "success", "experiments": experiments}


def get_last_entry_ids(session_id, experiment_id, entry_count):
	session_id = uuid.UUID(bytes=_uni2bin(session_id))
	#FIXME we most likely want to use a view here.
	_cursor.execute("""SELECT res_id
	FROM `exp_result`
	INNER JOIN `experiments`
	ON experiments.expr_id = exp_result.expr_id
	INNER JOIN `projects`
	ON projects.project_id = experiments.project_id
	INNER JOIN `project_group`
	ON project_group.project_id = projects.project_id
	INNER JOIN `user_group`
	ON user_group.group_id = project_group.group_id
	INNER JOIN `user`
	ON user_group.user_id = user.user_id
	INNER JOIN `user_session`
	ON user_session.user_id = user.user_id
	WHERE user_session.authorized = True AND user_session.session_id = %s""", session_id.bytes)
	entry_ids = _cursor.fetchall()
	return {"status": "success", "entry_ids": entry_ids}


def get_entry(session_id, entry_id):
	return {"status": "success"}
