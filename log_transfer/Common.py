import os,httplib,urllib2,urllib,time

class HTTPSClientAuthHandler(urllib2.HTTPSHandler):
    def __init__(self, key, cert):
        urllib2.HTTPSHandler.__init__(self)
        self.key = key
        self.cert = cert

    def https_open(self, req):
        # Rather than pass in a reference to a connection class, we pass in
        # a reference to a function which, for all intents and purposes,
        # will behave as a constructor
        return self.do_open(self.getConnection, req)

    def getConnection(self, host, timeout=300):
        return httplib.HTTPSConnection(host, key_file=self.key, cert_file=self.cert)

class Request:
    def __init__(self):
        proxy = os.getenv('X509_USER_PROXY')
        if not proxy:
            proxy = "/tmp/x509up_u%s" % os.geteuid()

        self.opener = urllib2.build_opener(HTTPSClientAuthHandler(proxy,proxy))

    # get method to parse given url which requires certificate
    def send(self, url,params=None):
        data = None
        try:
            if params:
                response = self.opener.open(url, urllib.urlencode(params))
            else:
                response = self.opener.open(url)

            data = response.read()

        except urllib2.HTTPError as e:
            Logger.log('Operation failed url: %s reason: HTTPError, %s' % (url, e.read()))
        except Exception as e:
            Logger.log('Operation failed url: %s reason: %s' % (url, e))

        return data

class Logger:
    @staticmethod
    def log(str):
        print time.strftime("%Y-%m-%d %H:%M:%S"),str
