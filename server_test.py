__author__ = "Frederik Lauber"
__copyright__ = "Copyright 2014"
__license__ = "GPL3"
__version__ = ""
__maintainer__ = "Frederik Lauber"
__status__ = "Development"
__contact__ = "https://flambda.de/impressum.html"

import scon_actions

(user_id, salt) = scon_actions._get_userid_and_salt("fredi1@uni-siegen.de")
print(user_id)
print(salt)
challenge = scon_actions.get_challenge("fredi1@uni-siegen.de")
print(challenge)