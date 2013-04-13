import re
import hashlib
import logging


class Utils:
    """ some string tidyin stuff and pasword hashing and salting using sha254 """

    ha1 = "pr3-5 a l t"
    ha2 = "p05t-5 a l t"

    def getNewPassHash(self, passwordtocheck, username):
        m = hashlib.sha256()

        good = False
        try:
            salted = self.ha1 + passwordtocheck + ":" + username + self.ha2

            m.update(salted.encode('utf8'))

            good = True
        except Exception, e:
            logging.warn(e)
            good = False
        
        return m.hexdigest()


    def cleanEmail(self, inmail):

        mail = self.tidyUserName(inmail)
        mailtocheck = mail.lower()
        return mailtocheck


    def strip_tags(self, value):
        """Returns the given HTML with all tags stripped."""
        stripped = re.sub(r'<[^>]*?>', ' ', value)
        return " ".join(stripped.split())


    def validateEmail(self, inmail):

        return True

    # can use this for urls and ids
    def cleanUserName(self, inuser):

        user = self.tidyUserName(inuser)
        # normuser = re.sub(r'\W+', '', user)
        normuser = re.sub('[^0-9a-zA-Z\-\s_]', '', user)

        usertocheck = normuser.lower().replace(' ', '-')

        return usertocheck

    # can use this for display 
    def tidyUserName(self, inuser):
        user = inuser.lstrip().rstrip()
        user = user.lstrip('-').rstrip('-')  # strip leading and trailing stuff

        user = user.expandtabs(1)

        # replace more than one space with one space
        user = " ".join(user.split())

        return user

    def validateUserName(self, inuser):
        allGood = True
        inuser = inuser.lower()

        if len(inuser) > 30:
            allGood = False

        if allGood:
            try:
                inuser.decode('ascii')
                try:
                    inuser.decode('ascii') #TODO - hmmm - strange coding by coincidence- tidy up required?
                except UnicodeDecodeError, e:
                    allGood = False
            except UnicodeEncodeError, e:
                allGood = False

        if allGood:
            reg=re.compile('^[a-z0-9_\-\.]+$')
            if not reg.match(inuser):
                allGood = False

        return allGood
