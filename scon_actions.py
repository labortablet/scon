#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "Frederik Lauber"
__copyright__ = "Copyright 2014"
__license__ = "?"
__version__ = ""
__maintainer__ = "Frederik Lauber"
__status__ = "Development"
__contact__ = "https://flambda.de/impressum.html"

import pymysql
import uuid
import configparser
import hashlib
import base64
import cgitb
cgitb.enable()

SERVER_STABLE_RANDOM = u"sadsdasdassadsd"


class LabletBaseException(Exception):
	pass


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


#key = uuid.uuid4()
#print 'inserting', repr(key.bytes)
#r = conn.cursor()
#r.execute('INSERT INTO xyz (id) VALUES (%s)', key.bytes)
#conn.commit()

#print 'selecting', repr(key.bytes)
#r.execute('SELECT added_id, id FROM xyz WHERE id = %s', key.bytes)
#for row in r.fetchall():
#    print row[0], binascii.b2a_hex(row[1])


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
	"session_id": base64.b64encode(session_id).decode("ascii"), 
	"salt":  base64.b64encode(salt).decode("ascii"), 
	"challenge": base64.b64encode(challenge).decode("ascii")}


def auth_session(session_id, response):
	#FIXME not yet implemented as database is not far enought yet
	return {"status": "success"}

def get_projects(session_id):
	session_id_base64 = base64.b64decode(session_id.encode("ascii"))
	session_id = uuid.UUID(bytes=session_id_base64)
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

def get_last_entry_ids(session_id, entry_count):
	return {"status": "success"}

def get_entry(session_id, entry_id):
	return {"status": "success"}

action_dict = {"test": test,
               "get_entry": get_entry,
               "get_last_entry_ids": get_last_entry_ids,
               "get_projects": get_projects,
               "auth_session": auth_session,
               "get_challenge":get_challenge}

