#!/usr/bin/env python
"""
Popularity client.
Perform SSO Authentication and retrieve data from API
"""
from subprocess import Popen, PIPE
from sys import argv, exit, stderr, version_info
from urllib2 import HTTPCookieProcessor, AbstractHTTPHandler, \
                    urlopen, build_opener, install_opener
from urllib import urlencode
from urlparse import urljoin
import os, re
try:
  from httplib import HTTPSConnection
except:
  from httplib import HTTPS as HTTPSConnection

DEBUG = False
ssl_key_file = None
ssl_cert_file = None

if DEBUG:
  def debug_init(self, **kwargs): self._debuglevel = 1
  AbstractHTTPHandler.__init__ = debug_init

class X509HTTPS(HTTPSConnection):
  def __init__(self, host, *args, **kwargs):
    HTTPSConnection.__init__(self, host, key_file = ssl_key_file,
                 cert_file = ssl_cert_file, **kwargs)

class X509Auth(AbstractHTTPHandler):
  def default_open(self, req):
    return self.do_open(X509HTTPS, req)

class Login:
    is_auth = False

    def __init__(self):
      global ssl_key_file
      global ssl_cert_file
      if not ssl_key_file:
        x509_path = os.getenv("X509_USER_KEY", None)
        if x509_path and os.path.exists(x509_path):
          ssl_key_file = x509_path

      if not ssl_cert_file:
        x509_path = os.getenv("X509_USER_CERT", None)
        if x509_path and os.path.exists(x509_path):
          ssl_cert_file = x509_path

      if not ssl_key_file:
        x509_path = os.getenv("HOME") + "/.globus/userkey.pem"
        if os.path.exists(x509_path):
          ssl_key_file = x509_path

      if not ssl_cert_file:
        x509_path = os.getenv("HOME") + "/.globus/usercert.pem"
        if os.path.exists(x509_path):
          ssl_cert_file = x509_path

      if not ssl_key_file or not os.path.exists(ssl_key_file):
        print >>stderr, "no certificate private key file found"
        exit(1)

      if not ssl_cert_file or not os.path.exists(ssl_cert_file):
        print >>stderr, "no certificate public key file found"
        exit(1)

    def getUrl(self,url):
        if self.is_auth:
            return urlopen(url).read()
        else:
            self.is_auth = True
            return self.sso_auth(url)

    def parse_form_fields(self,page):
      """Parses and decodes HTML form inputs with 'name' and 'value'."""
      result = {}
      for item in page.split('<input '):
        if item.find('name=') != -1 and item.find('value=') != -1:
          key = item.split('name="')[1].split('"')[0]
          val = item.split('value="')[1].split('"')[0] \
                .replace('&quot;', '"').replace('&lt;','<')
          result[key] = val
      return result

    def sso_auth(self,auth_url):
      """Authenticate to CERN SSO for `url` and retrieve data"""
      # Setup HTTP handlers
      cookieproc = HTTPCookieProcessor()
      opener = build_opener(cookieproc)
      opener.addheaders = [('User-agent', 'Mozilla/5.0')]
      install_opener(opener)

      # Send the first request which sets the auth cookie and leads to
      # redirection ending at CERN SSO login page. Grab the cert login
      # link from that page.
      login = urlopen(auth_url)
      login_page = login.read()
      m = re.search(r'href="(auth/sslclient/[^"]*)"', login_page)
      assert m, "No cert login link at <%s>" % login.geturl()
      login_url = urljoin(login.geturl(), m.group(1).replace("&amp;", "&"))

      # Redo opener to include X509 cert auth. Keep cookies.
      opener = build_opener(cookieproc, X509Auth())
      opener.addheaders = [('User-agent', 'Mozilla/5.0')]
      install_opener(opener)

      # Now login with cert. This sets authentication cookie, and yields
      # a form we are meant to re-submit to complete the authentication.
      jump_page = urlopen(login_url).read()

      sso_data = self.parse_form_fields(jump_page)
      m = re.search(r'<form[^>]* action="([^"]*?)">', jump_page)
      assert m, "No form to post after sso auth?"
      master_url = m.group(1)

      # Reset opener to remove the X509 authentication but keep cookies.
      opener = build_opener(cookieproc)
      opener.addheaders = [('User-agent', 'Mozilla/5.0')]
      install_opener(opener)

      # Read document.
      document = urlopen(master_url, urlencode(sso_data))
      pop_data = document.read()
      return pop_data
