import math
import json
import logging
from models.models import Content

class Widgets():
    """ functions to populate the data that will be passed to the templates for the respective widgets to render """

    def __init__(self, router, conf):
        self._conf = conf
        self._req = router._req                 # TODO - this is private so......
        self._router = router

    
    def popular(self):

        popular = {}
        pop = Content.get_by_key_name("popular-articles")
        if pop:
             
            popular['data'] = pop.current
            popular['articles'] = []
            
            try:
                popobj = json.loads(pop.current.content)
                for po in popobj:
                    po_cont = Content.get_by_key_name(po)
                    po_cont.current.group = po_cont.group
                    po_cont.current.keyname = po_cont.key().name()
                    popular['articles'].append(po_cont.current)

            except Exception, e:
                logging.error('popular problem')
                logging.exception(e)

        return popular


    def pagination(self, acount):
        
        curpage = self._router._curpage
        
        pagecount = int(math.ceil(float(acount)/self._router._PAGESIZE))

        pclass = 'disabled'
        nclass = 'disabled'

        plink = ''
        nlink = ''

        if pagecount > 1:
            ppage = curpage - 1
            if ppage > 0:
                pclass = ''
                plink = self._req.setpar("p", str(ppage))

            npage = curpage + 1
            if npage <= pagecount:
                nclass = ''
                nlink = self._req.setpar("p", str(npage))

        pages = []
        for p in range(1, pagecount + 1):
            pp = {
                'hclass': '',
                'link': self._req.setpar("p", str(p)),
                'num': p
            }
            if p == curpage:
                pp['hclass'] = 'active'
            pages.append(pp)
            
        return {
            'articlecount': acount,
            'pagecount': pagecount,
            'curpage': curpage,
            'plist': pages,
            'next': {
                'hclass': nclass,
                'link': nlink
            },
            'prev': {
                'hclass': pclass,
                'link': plink
            }
        }

    
    def slider(self, q):
        SLIDERCOUNT = 4

        slider = []
        for c in q.fetch(SLIDERCOUNT, offset=0):
            d = self._router.copy_bits(c)
            slider.append(d)

        return slider


 