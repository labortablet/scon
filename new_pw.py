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

import pymysql


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


@_enable_db
def new_pw(user, password):
	salt = uuid.uuid4().bytes
	hash_pw = hashlib.sha256(password).digest()
	#salted_pw = bcrypt.hashpw(hash_pw, bcrypt.gensalt(10, salt))
	salted_pw = hashlib.sha256(salt + hash_pw).digest()
	_cursor.execute("""UPDATE users SET salt = %s, hash_password = %s WHERE email = %s""", (salt, salted_pw, user))
	_database.commit()


@_enable_db
def get_usernames():
	_cursor.execute("""SELECT email FROM `users`""")
	return tuple(i[0] for i in _cursor.fetchall())


while True:
	names = get_usernames()
	letters = len(str(len(names)))
	for num, name in enumerate(names):
		print(str(num).zfill(letters), ": ", name)
	select = int(input("Give number to change PW:"))
	if select < len(names):
		pw = input("Type Password")
		new_pw(names[select], pw.encode("utf-8"))
		print("PW changed!")

