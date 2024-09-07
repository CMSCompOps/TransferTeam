#!/usr/bin/env python
import sys
import socket
import dns.resolver

if __name__ == "__main__":
    h="xrootd-cms.infn.it"
    h="cms-xrootd.gridpp.ac.uk"
    if len(sys.argv) > 1 :
        h=sys.argv[1]
    result = dns.resolver.resolve(h, 'A')
    for ipval in result:
        ip = ipval.to_text()
        (host, alias, ipl) = socket.gethostbyaddr(ip)
        print ( host, alias, ipl )
