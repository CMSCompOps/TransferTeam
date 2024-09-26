import os
import sys
import urllib
import urllib2
import httplib
import json

# Sites to have links to/from disabled completely
disabled_nodes = ['T2_BR_UERJ', 'T2_RU_PNPI', 'T2_RU_SINP', 'T2_TH_CUNSTDA'] # [node]
# Specific links to disable
disabled_links = [] # [(to, from)]
# Sites to not touch (e.g. being commissioned) - T3s are also skipped
skipped_nodes = ['T2_PK_NCP']

x509_proxy = '/tmp/x509up_u%d' % os.getuid()

def httpsconnection(host, timeout = 0):
    return httplib.HTTPSConnection(host, key_file = x509_proxy, cert_file = x509_proxy)

class X509Handler(urllib2.HTTPSHandler):
    def https_open(self, request):
        return self.do_open(httpsconnection, request)

def datasvc(command, args = []):
    url = 'https://cmsweb.cern.ch/phedex/datasvc/json/prod/' + command
    if len(args):
        url += '?' + '&'.join(args)

    request = urllib2.Request(url)
    
    opener = urllib2.build_opener(X509Handler())
    opener.addheaders.append(('Accept', 'application/json'))
    response = opener.open(request)
    
    return json.loads(response.read())['phedex']

if __name__ == '__main__':
    from argparse import ArgumentParser

    argParser = ArgumentParser(description = 'Dump the link commands.')
    argParser.add_argument('--current', '-c', action = 'store_true', dest = 'current', help = 'Dump current state.')

    args = argParser.parse_args()
    sys.argv = []

    result = datasvc('nodes')
    nodes = sorted(n['name'] for n in result['node'] if not n['name'].startswith('T3') and n['name'] not in skipped_nodes)
    
    result = datasvc('links')
    links = {}
    for link in result['link']:
        links[(link['from'], link['to'])] = link['status']
    
    for from_node in list(nodes):
        if from_node != 'T2_PK_NCP':
            continue

        for to_node in list(nodes):
            try:
                current = links[(from_node, to_node)]
            except KeyError:
                continue

            # Will not touch links that are not in ok or deactivated states
            if current not in ['ok', 'deactivated']:
                continue

            if args.current:
                if current == 'ok':
                    print from_node, to_node, 'enable'
                else:
                    print from_node, to_node, 'disable'

            else:
                if from_node in disabled_nodes or to_node in disabled_nodes or (from_node, to_node) in disabled_links:
                    print from_node, to_node, 'disable'
                else:
                    print from_node, to_node, 'enable'
