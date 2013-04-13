from google.appengine.api import mail


class Emails():
    def __init__ (self, req):
        self.req = req

# TODO - put these in templates
    
    def contact (self):
        selTypes = self.req.par("selTypes")
        txtSubject = self.req.par("txtSubject")
        txtName = self.req.par("txtName")
        txtEmail = self.req.par("txtEmail")
        txtMessage = self.req.par("txtMessage")

        bod = "Hi " + txtName + """
                    
Thanks a lot for contacting us. We'll be in touch very soon. 

For info here's a copy of the details of you filled out...

Type: {0}

Subject: {1}

your Name: {2}

your Email: {3}

Your Message: 

{4}

Cheers.
The My site Team.
(p.s. If you didnt contact us, drop us a line and we'll deal with it.)
"""

        bod = bod.format(selTypes, txtSubject, txtName, txtEmail, txtMessage)
        recipient = txtName + " <" + txtEmail + ">"
        try:
            mail.send_mail(sender="My site Info <info@My site.com>",
                          to=recipient,
                          subject="Thanks for Your Contact.",
                          body=bod
                          )

            mail.send_mail(sender="My site Info <info@My site.com>",
                          to="My site Info <info@My site.com>",
                          subject="Contact form Filled In.",
                          body=bod
                          )
        except Exception, e:
            logging.error('Email not sent"')
            logging.exception(e)


    