#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "Frederik Lauber"
__copyright__ = "Copyright 2014"
__license__ = "?"
__version__ = ""
__maintainer__ = "Frederik Lauber"
__status__ = "Development"
__contact__ = "https://flambda.de/impressum.html"
# FIXME document which modules need to be installed for this

import uuid
import configparser
import hashlib
import base64
import cgitb

import pymysql
import bcrypt


cgitb.enable()

class LabletBaseException(Exception):
	pass


#encode and decode a binary as a abs64 encoded string
#will return a unicode object so we are independent from transmission encoding
def _uni2bin(uni):
	return base64.b64decode(uni.encode("ascii"))


def _bin2uni(bin):
	return base64.b64encode(bin).decode("ascii")


def _enable_db(func):
	global _SERVER_STABLE_RANDOM
	global _database
	global _cursor
	_config = configparser.ConfigParser()
	_config.read_file(open("/home/lablet/.my.cnf"))
	_SERVER_STABLE_RANDOM = _config.get('client', 'password')
	_database = pymysql.connect(unix_socket=_config.get('client', 'socket'),
                            port=_config.get('client', 'port'),
                            user=_config.get('client', 'user'),
                            passwd=_config.get('client', 'password'),
                            db="lablet_tabletprojectdb",
                            charset='utf8')
	del _config
	_cursor = _database.cursor()

	def do_nothing(func):
		return func

	_enable_db = do_nothing
	return func


@_enable_db
def _get_userid_and_salt(username):
	_cursor.execute("""SELECT id, salt FROM `users` WHERE email = %s""", username)
	user_list = _cursor.fetchall()
	if len(user_list) == 1:
		user_id = user_list[0][0]
		salt = user_list[0][1]
		return user_id, salt
	else:
		m = hashlib.md5()
		m.update(username.encode("utf-8"))
		m.update(_SERVER_STABLE_RANDOM.encode("utf-8"))
		salt = m.digest()
		return None, salt


def echo(**kwargs):
	return kwargs


def version(**kwargs):
	return {"status": "success", "version": "0.2"}


@_enable_db
def get_challenge(username):
	session_id = uuid.uuid4().bytes
	challenge = uuid.uuid4().bytes
	(user_id, salt) = _get_userid_and_salt(username)
	try:
		_cursor.execute(
			"""INSERT INTO sessions(id, challenge, user_id, authorized) VALUES (%s,%s,%s, True)""",
			(session_id, challenge, user_id))
		_database.commit()
	except Exception:
		return {"status": "failed"}
	else:
		return {"status": "success",
		        "session_id": _bin2uni(session_id),
	        "salt": _bin2uni(salt),
	        "challenge": _bin2uni(challenge)}


@_enable_db
def auth_session(session_id, response):
	session_id = uuid.UUID(bytes=_uni2bin(session_id))
	_cursor.execute("""SELECT
	users.hash_password,
	sessions.challenge
	FROM `users`
	INNER JOIN `sessions`
	ON sessions.user_id = users.id
	WHERE sessions.id = %s""", session_id.bytes)
	(hash_password, challenge) = _cursor.fetchall()[0]
	if response == bcrypt.hashpw(hash_password, bcrypt.gensalt(10, _uni2bin(challenge))):
		try:
			_cursor.execute("""UPDATE sessions SET authorized = True WHERE session_id = %s""", session_id)
			_database.commit()
		except Exception:
			return {"status": "failed"}
		else:
			return {"status": "success"}
	else:
		return {"status": "failed"}


@_enable_db
def get_user(session_id):
	session_id = uuid.UUID(bytes=_uni2bin(session_id))
	_cursor.execute("""SELECT
	lastname,
	firstname,
	profil_image,
	create_date,
	email
	FROM `users`
	INNER JOIN `sessions`
	ON sessions.user_id = user.id
	WHERE sessions.authorized = True AND sessions.id = %s""", session_id.bytes)
	user_info = _cursor.fetchall()[0]
	return {"status": "success", "user": user_info}


@_enable_db
def get_projects(session_id):
	session_id = uuid.UUID(bytes=_uni2bin(session_id))
	_cursor.execute("""SELECT
	users_projects_view.project_id,
	users_projects_view.project_name,
	users_projects_view.project_description
	FROM `users_projects_view`
	INNER JOIN `sessions`
	ON sessions.user_id = users_projects_view.user_id
	WHERE sessions.authorized = True AND sessions.id = %s""", session_id.bytes)
	projects = _cursor.fetchall()
	return {"status": "success", "projects": projects}


@_enable_db
def get_experiments(session_id):
	session_id = uuid.UUID(bytes=_uni2bin(session_id))
	_cursor.execute("""SELECT
	users_experiments_view.experiment_id,
	users_experiments_view.experiment_name,
	users_experiments_view.experiment_description
	FROM `users_experiments_view`
	INNER JOIN `sessions`
	ON users_experiments_view.user_id = sessions.user_id
	WHERE sessions.authorized = True AND sessions.id = %s""", session_id.bytes)
	experiments = _cursor.fetchall()
	return {"status": "success", "experiments": experiments}


@_enable_db
def get_last_entry_ids(session_id, experiment_id, entry_count):
	experiment_id = int(experiment_id)
	entry_count = int(entry_count)
	session_id = uuid.UUID(bytes=_uni2bin(session_id))
	_cursor.execute("""SELECT
	entry_id
	FROM `users_groups_entries_view`
	WHERE users_groups_entries_view.experiment_id = %s AND group_id IN
	(SELECT DISTINCT group_id
	FROM users_groups WHERE user_id IN
	(SELECT user_id
	FROM sessions
	WHERE
	sessions.authorized = True AND sessions.id = %s))
	ORDER BY users_groups_entries_view.entry_date, users_groups_entries_view.entry_date_user DESC LIMIT %s""",
	                (experiment_id, session_id.bytes, entry_count))
	# get and flatten
	entry_ids = tuple(i[0] for i in _cursor.fetchall())
	return {"status": "success", "entry_ids": entry_ids}


@_enable_db
def get_entry(session_id, entry_id):
	entry_id = int(entry_id)
	session_id = uuid.UUID(bytes=_uni2bin(session_id))
	_cursor.execute("""SELECT
	user_firstname,
	user_lastname,
	user_email,
	group_name,
	group_description,
	project_id,
	experiment_id,
	entry_title,
	entry_date,
	entry_date_user,
	entry_attachment,
	entry_attachment_type
	FROM `users_groups_entries_view`
	WHERE users_groups_entries_view.entry_id = %s AND group_id IN
	(SELECT DISTINCT group_id
	FROM users_groups WHERE user_id IN
	(SELECT user_id
	FROM sessions
	WHERE
	sessions.authorized = True AND sessions.id = %s))""", (entry_id, session_id.bytes))
	entry_list = _cursor.fetchall()
	if len(entry_list) > 1:
		raise Exception("Entry id not unique")
	entry = entry_list[0]
	(user_firstname,
	 user_lastname,
	 user_email,
	 group_name,
	 group_description,
	 project_id,
	 experiment_id,
	 entry_title,
	 entry_date,
	 entry_date_user,
	 entry_attachment,
	 entry_attachment_type) = entry_list[0]
	return {"status": "success",
	        "user_firstname": user_firstname,
	        "user_lastname": user_lastname,
	        "user_email": user_email,
	        "group_name": group_name,
	        "group_description": group_description,
	        "project_id": project_id,
	        "experiment_id": experiment_id,
	        "entry_title": entry_title,
	        "entry_date": entry_date,
	        "entry_date_user": entry_date_user,
	        "entry_attachment": entry_attachment,
	        "entry_attachment_type": entry_attachment_type}