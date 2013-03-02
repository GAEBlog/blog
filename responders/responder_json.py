import json
import urllib
import logging


class JSONResponder():
    
    def __init__(self, conf, resp):
        self._resp = resp
        self._conf = conf
        

    def draw(self, path, obj={}, opt={}):
        """ path and opt unused but so its consistent with other responders """
    	
        self.draw_body("success", "ok", obj)
        

    def draw_code(self, code="success", message="ok", obj={}):
        self.draw_body(code, message, obj)


    def draw_body(self, code="none", message="nothing", obj={}):
        reply = {
            "code": code,
            "message": message,
            "payload": obj
        }
        self._send(json.dumps(reply, indent=2))


    def _send(self, body):
        self._resp.headers["Content-Type"] = "application/json"
        self._resp.headers["Access-Control-Allow-Origin"] = self._conf.DOMAIN
        
        self._resp.out.write(body)


    def blast(self, content):
        self._resp.out.write(content)


    def notfound(self):
        self.draw(path="", obj={"code": "bad", "message": "Resource not found"})


    def unauthorised(self):
        self.draw(path="", obj={"code": "bad", "message": "Unauthorised"})
