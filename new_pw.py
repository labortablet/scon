__author__ = "Frederik Lauber"
__copyright__ = "Copyright 2014"
__license__ = "GPL3"
__version__ = ""
__maintainer__ = "Frederik Lauber"
__status__ = "Development"
__contact__ = "https://flambda.de/impressum.html"

import uuid
import hashlib

from scon_actions import _enable_db
import bcrypt


username = "fredi@uni-siegen.de"
pw = "test"


@_enable_db
def new_pw(user, password):
	salt = uuid.uuid4().bytes
	hash_pw = hashlib.sha256(password).digest()
	salted_pw = bcrypt.hashpw(hash_pw, bcrypt.gensalt(10, salt))
	_cursor.execute("""UPDATE users SET salt = %s, hash_password = %s WHERE email = %s""", (salt, salted_pw, user))
	_database.commit()


new_pw(username, pw)