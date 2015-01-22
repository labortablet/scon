#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "Frederik Lauber"
__copyright__ = "Copyright 2014"
__license__ = "?"
__version__ = "0.2"
__maintainer__ = "Frederik Lauber"
__status__ = "Development"
__contact__ = "https://flambda.de/impressum.html"
# FIXME document which modules need to be installed for this

import uuid
import configparser
import hashlib
import base64
import datetime

import pymysql


class LabletBaseException(Exception):
	pass

#encode and decode a binary as a abs64 encoded string
#will return a unicode object so we are independent from transmission encoding
def _uni2bin(uni):
	return base64.b64decode(uni.encode("ascii"))


def _bin2uni(bin):
	return base64.b64encode(bin).decode("ascii")

def _removeAttachment(attachment_ref, attachment_type):
	pass

def _putAttachment(attachment, attachment_type):
	attachment_ref = "foo"
	return attachment_ref

def _getAttachment(attachment_ref, attachment_type):
	#only text right now
	#needs to return a str object
	return attachment_ref

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
			"""INSERT INTO sessions(id, challenge, user_id) VALUES (%s,%s,%s)""",
			(session_id, challenge, user_id))
		_database.commit()
	except Exception as E:
		return {"status": "failed", "E": str(E)}
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
	tmp = hashlib.sha256(challenge + hash_password).digest()
	if _uni2bin(response) == tmp:
		try:
			_cursor.execute("""UPDATE sessions SET authorized = True WHERE sessions.id = %s""", session_id.bytes)
			_database.commit()
		except Exception as E:
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
	users_experiments_view.project_id,
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
	entry_id, entry_current_time
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
	entry_id_timestamps = tuple((i[0], 0 if i[1] is None else i[1].timestamp()) for i in _cursor.fetchall())
	return {"status": "success", "entry_id_timestamps": entry_id_timestamps}


@_enable_db
def get_entry(session_id, entry_id, entry_change_time):
	#entry_change_time is not used right now
	#but might be used to get
	#a specific version of the entry
	try:
		entry_id = int(entry_id)
		session_id = uuid.UUID(bytes=_uni2bin(session_id))
		_cursor.execute("""SELECT
		user_firstname,
		user_lastname,
		experiment_id,
		entry_title,
		entry_date,
		entry_date_user,
		entry_current_time,
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
		 experiment_id,
		 entry_title,
		 entry_date,
		 entry_date_user,
		 entry_current_time,
		 entry_attachment_ref,
		 entry_attachment_type) = entry_list[0]
		attachment = _getAttachment(entry_attachment_ref, entry_attachment_type)
		return {"status": "success",
		        "user_firstname": user_firstname,
		        "user_lastname": user_lastname,
		        "experiment_id": experiment_id,
		        "entry_title": entry_title,
		        "entry_date": str(entry_date),
		        "entry_date_user": str(entry_date_user),
		        "entry_current_time": str(entry_current_time),
		        "entry_attachment": attachment,
		        "entry_attachment_type": entry_attachment_type}
	except Exception as E:
		return {"status": "failed", "E":str(E)}

@_enable_db
def send_entry(session_id, title, date_user, attachment, attachment_type, experiment_id):
	#maybe this could also be done in mysql?
	#not sure right now so I will do it like this
	check = get_experiments(session_id)
	if not check["status"] == "success":
		raise Exception
	valid_experiment = False
	experiment_id = int(experiment_id)
	for experiment in check["experiments"]:
		if int(experiment[1]) == experiment_id:
			valid_experiment = True
			break
	if not valid_experiment:
		raise Exception
	#so we are allowed to add to this experiment
	session_id = uuid.UUID(bytes=_uni2bin(session_id))
	#check we do not have a double sync
	#rememeber, date_user is supposed to be unique within a experiment as stupid as
	#it sounds.....
	_cursor.execute("""SELECT
	entry_id, entry_current_time
	FROM `users_groups_entries_view`
	WHERE users_groups_entries_view.experiment_id = %s AND entry_date_user = %s """,
	                (experiment_id, date_user))
	res = _cursor.fetchall()
	if len(res) > 1:
		#this should never happen!
		return {"status": "failure", "info": "WTF? Check your bloddy database!"}
	elif len(res) == 1:
		return {"status": "success", "info": "double sync", "entry_id": str(res[0][0]), "entry_current_time": str(res[0][1])}
	current_time = datetime.datetime.utcnow()
	date_user = datetime.datetime.utcfromtimestamp(int(date_user))
	#we might need to find a way to safely remove atatchments if the db fails
	attachment_ref = _putAttachment(attachment, attachment_type)
	_cursor.execute("""INSERT INTO
		`entries`
		(title,
		date,
		date_user
		current_time,
		attachment,
		attachment_type,
		expr_id,
		user_id)
		VALUES (%s,'%s','%s','%s',%s, %s, %s,
			(SELECT user_id
			FROM sessions
			WHERE
			sessions.authorized = True AND sessions.id = %s);SELECT LAST_INSERT_ID()
		""", (
	title, current_time, date_user, current_time, attachment_ref, attachment_type, experiment_id, session_id.bytes))
	res = _cursor.fetchall()
	return {"status": "success", "entry_id": str(res[0][0]), "entry_current_time": str(res[0][1])}
	#except Exception as E:
	#	return {"status": "failed", "E":str(E)}
