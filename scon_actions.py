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

_file_folder = "/home/lablet/sconfiles"


import uuid
import configparser
import hashlib
import base64
import datetime
import os

# attachment types:
# 	1 = text
# 	2 = tabular
# 	3 = picture
# 	4 = file
# 	5 = video

try:
	import pymysql
except ImportError:
	pymysql = None

_mysql_timestring = '%Y-%m-%d %H:%M:%S'

class LabletBaseException(Exception):
	pass


# encode and decode a binary as a abs64 encoded string
#will return a unicode object so we are independent from transmission encoding
def _uni2bin(uni):
	return base64.b64decode(uni.encode("ascii"))


def _bin2uni(bin):
	return base64.b64encode(bin).decode("ascii")


def _hash_password(password):
	return hashlib.sha256(password).digest()


def _salted_password(password, salt):
	hash_pw = _hash_password(password)
	#salted_pw = bcrypt.hashpw(hash_pw, bcrypt.gensalt(10, salt))
	return hashlib.sha256(salt + hash_pw).digest()


def _challenge_response(salted_password, challenge):
	return hashlib.sha256(challenge + salted_password).digest()

def _removeAttachment(attachment_ref, attachment_type):
	if attachment_type == 1 or attachment_type == 2:
		pass
	elif attachment_type == 3 or attachment_type == 4 or attachment_type == 5:
		os.remove(os.path.join(_file_folder, attachment_ref))


def _putAttachment(attachment, attachment_type):
	attachment_ref = None
	if attachment_type == 1 or attachment_type == 2:
		attachment_ref = attachment
	elif attachment_type == 3 or attachment_type == 4 or attachment_type == 5:
		filename = uuid.uuid4()
		while os.path.exists(os.path.join(_file_folder, filename)):
			filename = uuid.uuid4()
		with open(os.path.join(_file_folder, filename), "w") as file:
			file.write(attachment)
			attachment_ref = filename
	return attachment_ref


def _getAttachment(attachment_ref, attachment_type):
	if attachment_type == 1 or attachment_type == 2:
		return attachment_ref
	elif attachment_type == 3 or attachment_type == 4 or attachment_type == 5:
		with open(os.path.join(_file_folder, attachment_ref), "r") as file:
			return file.read()

if pymysql is not None:
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
else:
	def _enable_db(func):
		def nomysql(**args):
			raise RuntimeError
		return nomysql


@_enable_db
def _get_userid_and_salt(username):
	username = str(username)
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

@_enable_db
def _get_authed_session(username):
	session_id = uuid.uuid4().bytes
	(user_id, salt) = _get_userid_and_salt(username)
	_cursor.execute(
		"""INSERT INTO sessions(id, user_id, authorized) VALUES (%s,%s,True)""",
		(session_id, user_id))
	_database.commit()
	return _bin2uni(session_id)


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
	(salted_password, challenge) = _cursor.fetchall()[0]
	if _uni2bin(response) == _challenge_response(salted_password, challenge):
		_cursor.execute("""UPDATE sessions SET authorized = True WHERE sessions.id = %s""", session_id.bytes)
		_database.commit()
		return {"status": "success"}
	else:
		return {"status": "failed", "Info": "Password seems to be incorrect"}


def echo(**kwargs):
	return kwargs


def version(**kwargs):
	return {"status": "success", "version": "0.2"}


@_enable_db
def get_challenge(username):
	session_id = uuid.uuid4().bytes
	challenge = uuid.uuid4().bytes
	(user_id, salt) = _get_userid_and_salt(username)
	_cursor.execute(
		"""INSERT INTO sessions(id, challenge, user_id) VALUES (%s,%s,%s)""",
		(session_id, challenge, user_id))
	_database.commit()
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
	(salted_password, challenge) = _cursor.fetchall()[0]
	if _uni2bin(response) == _challenge_response(salted_password, challenge):
		_cursor.execute("""UPDATE sessions SET authorized = True WHERE sessions.id = %s""", session_id.bytes)
		_database.commit()
		return {"status": "success"}
	else:
		return {"status": "failed", "Info": "Password seems to be incorrect"}


@_enable_db
def get_user(session_id):
	session_id = uuid.UUID(bytes=_uni2bin(session_id))
	_cursor.execute("""SELECT
	lastname,
	firstname,
	profil_image,
	UNIX_TIMESTAMP(create_date),
	email
	FROM `users`
	INNER JOIN `sessions`
	ON sessions.user_id = users.id
	WHERE sessions.authorized = True AND sessions.id = %s""", session_id.bytes)
	(lastname, firstname, profil_image, create_date, email) = _cursor.fetchall()[0]
	return {"status": "success", "lastname": lastname, "firstname": firstname,
	        "create_date": str(create_date)}


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
	entry_id, UNIX_TIMESTAMP(entry_current_time)
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
	entry_id_timestamps = tuple((i[0], 0 if i[1] is None else i[1]) for i in _cursor.fetchall())
	return {"status": "success", "entry_id_timestamps": entry_id_timestamps}


@_enable_db
def check_auth(session_id):
	session_id = uuid.UUID(bytes=_uni2bin(session_id))
	_cursor.execute("""SELECT sessions.authorized FROM sessions WHERE sessions.id = %s""", (session_id.bytes))
	res = _cursor.fetchall()
	if len(res) > 1:
		# this should never happen!
		return {"status": "failure", "info": "WTF? Check your bloody database!"}
	elif len(res) == 1:
		if res[0][0] == 1:
			return {"status": "success", "auth": True}
		else:
			return {"status": "success", "auth": False}


@_enable_db
def get_entry(session_id, entry_id, entry_change_time):
	#entry_change_time is not used right now
	#but might be used to get
	#a specific version of the entry
	entry_id = int(entry_id)
	session_id = uuid.UUID(bytes=_uni2bin(session_id))
	_cursor.execute("""SELECT
	user_id,
	user_firstname,
	user_lastname,
	experiment_id,
	entry_title,
	UNIX_TIMESTAMP(entry_date),
	UNIX_TIMESTAMP(entry_date_user),
	UNIX_TIMESTAMP(entry_current_time),
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

	(user_id,
	 user_firstname,
	 user_lastname,
	 experiment_id,
	 entry_title,
	 entry_date,
	 entry_date_user,
	 entry_current_time,
	 entry_attachment_ref,
	 entry_attachment_type) = entry_list[0]

	attachment = _getAttachment(entry_attachment_ref, entry_attachment_type)

	entry_date = str(entry_date)
	entry_date_user = str(entry_date_user)
	entry_current_time = str(entry_current_time)

	return {"status": "success",
	        "user_id": user_id,
	        "user_firstname": user_firstname,
	        "user_lastname": user_lastname,
	        "experiment_id": experiment_id,
	        "entry_title": entry_title,
	        "entry_date": entry_date,
	        "entry_date_user": entry_date_user,
	        "entry_current_time": entry_current_time,
	        "entry_attachment": attachment,
	        "entry_attachment_type": entry_attachment_type}


@_enable_db
def send_entry(session_id, title, date_user, attachment, attachment_type, experiment_id):
	check = get_experiments(session_id)
	session_id = uuid.UUID(bytes=_uni2bin(session_id))
	cur_time = int(datetime.datetime.utcnow().timestamp())
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
	#check we do not have a double sync
	#rememeber, date_user is supposed to be unique within a experiment as stupid as
	#it sounds.....
	_cursor.execute("""SELECT
	entry_id, UNIX_TIMESTAMP(entry_current_time)
	FROM `users_groups_entries_view`
	WHERE users_groups_entries_view.experiment_id = %s AND entry_date_user = FROM_UNIXTIME(%s)""",
	                (experiment_id, date_user))
	res = _cursor.fetchall()
	if len(res) > 1:
		#this should never happen!
		return {"status": "failure", "info": "WTF? Check your bloody database!"}
	elif len(res) == 1:
		return {"status": "success", "info": "double sync", "entry_id": str(res[0][0]),
		        "entry_current_time": str(res[0][1])}
	# we might need to find a way to safely remove attachments if the db fails
	attachment_ref = _putAttachment(attachment, attachment_type)
	# INTO @id
	#
	_cursor.execute(
		"""SELECT sessions.user_id FROM `sessions` WHERE sessions.authorized = True AND sessions.id = %s""",
		(session_id.bytes))
	res = _cursor.fetchall()
	user_id = res[0][0]
	_cursor.execute("""INSERT INTO
		`entries`
		(
			`title`,
			`date`,
			`date_user`,
			`attachment`,
			`attachment_type`,
			`user_id`,
			`expr_id`,
			`current_time`
		)
		VALUES (%s, FROM_UNIXTIME(%s), FROM_UNIXTIME(%s), %s, %s, %s, %s, FROM_UNIXTIME(%s))""", (
	title, cur_time, int(date_user), attachment_ref, attachment_type, user_id, experiment_id, cur_time))
	_database.commit()
	return {"status": "success", "entry_id": str(_cursor.lastrowid),
	        "entry_current_time": str(cur_time)}

