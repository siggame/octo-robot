# 
# WebServerAuthenticator
# 
# Use this class to verify that a team's login/password combo
# is valid.
# 
import httplib
import urllib
import json
import hashlib

class WebServerException(Exception):
    def __init__(self, message):
        self.message = str(message)
    def __str__(self):
        return self.message

class WebServerAuthenticator(object):
    def __init__(self, web_server_url):
        """
        Params:
        web_server_url - the url of the siggame webserver
        """
        self.url = web_server_url
    
    def auth_team(self, login, passwd):
        """
        login - the team's login
        passwd - the team's password
        """
        # Make a connection to the specified URL
        conn = httplib.HTTPConnection(self.url)
        # Create a GET query string and send it...
        params = urllib.urlencode({'l': login, 
                                   'c': 'megaminerai-9-space',
                                   'p': passwd})
        try:
            conn.request("GET", "/api/competition/team/auth?"+params)
        except:
            m = "Couldn't connect to server at %s" % (self.url,)
            raise WebServerException(m)
        # Grab the response
        response = conn.getresponse() 
        if response.status != 200:
            # Error if it's not an "HTTP 200 OK" response
            m = "Webserver Error: HTTP %d %s" % (response.status,
                                                 response.reason)
            raise WebServerException(m)
        # Get the data out and check the responses.
        data = json.loads(response.read())
        conn.close()
        try:
            return data['name']
        except KeyError:
            return False
        except TypeError:
            return False

    
if __name__ == '__main__':
    w = WebServerAuthenticator('r99acm.device.mst.edu:9999')
    if w.auth_team('derp', 'ecBQfAvQ') == 'derp':
        print "PASSED: got derp"
    if  w.auth_team('derp', 'ecBQfAvQ______'):
        print "FAILED: got name: %s"%name
    else:
        print "PASSED: login was wrong"
        
