#!/usr/bin/env python
import socket
import dns.resolver
h="xrootd-cms.infn.it"
result = dns.resolver.resolve(h, 'A')
for ipval in result:
    ip = ipval.to_text()
    (host, alias, ipl) = socket.gethostbyaddr(ip)
    print ( host, alias, ipl )
