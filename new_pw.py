__author__ = "Frederik Lauber"
__copyright__ = "Copyright 2014"
__license__ = "GPL3"
__version__ = ""
__maintainer__ = "Frederik Lauber"
__status__ = "Development"
__contact__ = "https://flambda.de/impressum.html"

import uuid
import hashlib
import configparser

import bcrypt
import pymysql


username = "fredi@uni-siegen.de"
pw = "test".encode("utf-8")


def new_pw(user, password):
	salt = uuid.uuid4().bytes
	hash_pw = hashlib.sha256(password).digest()
	salted_pw = bcrypt.hashpw(hash_pw, bcrypt.gensalt(10, salt))
	config = configparser.ConfigParser()
	config.read_file(open("/home/lablet/.my.cnf"))
	database = pymysql.connect(unix_socket=config.get('client', 'socket'),
	                           port=config.get('client', 'port'),
	                           user=config.get('client', 'user'),
	                           passwd=config.get('client', 'password'),
	                           db="lablet_tabletprojectdb",
	                           charset='utf8')
	cursor = database.cursor()
	cursor.execute("""UPDATE users SET salt = %s, hash_password = %s WHERE email = %s""", (salt, salted_pw, user))
	database.commit()


new_pw(username, pw)