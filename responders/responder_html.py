import os
import urllib
import jinja2

# hard coded base host - to take advantage of GAE's cdn
# BASE_HOST='http://your-app.appspot.com'     # TODO must accomodate the current scheme
BASE_HOST=''

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), '../templates')))

class HTMLResponder():
    
    def __init__(self, conf, resp):
        self._resp = resp
        self._conf = conf

        
    def draw(self, path, obj={}, opt={}):

        fullpath = path.lower() + '.html'

        template_values = {
              # root to the app engine path (in case the blog is behind a reverse proxy)
              'cdn_url': BASE_HOST,
              
              'obj': obj,
              'opt': opt, 
              
              # cache busting version
              'css_ver' : '1',
              'lib_css_ver' : '1',
              'js_ver'  : '1'
            }

        template = jinja_environment.get_template(fullpath)
        
        html = template.render(template_values)

        self._resp.out.write(html)

        return html


    def blast(self, content):
        self._resp.out.write(content)


    def notfound(self):
        self.draw(path="404")


    def unauthorised(self):
        self.draw(path='unauthorised')
