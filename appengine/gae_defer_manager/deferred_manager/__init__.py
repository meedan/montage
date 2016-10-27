import webapp2

from . import api

from .wrapper import defer

class HomeHandler(webapp2.RequestHandler):
    def get(self):
        url = self.request.url
        if not url.endswith("/"):
            url += "/"
        self.redirect(url + 'static/index.html')

application = webapp2.WSGIApplication([
    ('.+/api/logs/([\w\d-]+)', api.LogHandler),
    ('.+/api/([\w\d-]+)/([\w\d-]+)', api.TaskInfoHandler),
    ('.+/api/([\w\d-]+)', api.QueueHandler),
    ('.+/api.*', api.QueueListHandler),
    ('.*', HomeHandler),
])
