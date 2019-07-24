# -*- coding: UTF-8 -*-
import socket
from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol


class Echo(DatagramProtocol):
    def datagramReceived(self, data, addr):
        print("received %r from %s" % (data, addr))
        self.transport.write(data, addr)

reactor.listenUDP(1234, Echo())
reactor.run()

"""
portSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
portSocket.setblocking(False)
portSocket.bind(("127.0.0.1", 1234))

port = reactor.adoptDatagramPort(portSocket.fileno(), socket.AF_INET, Echo())
portSocket.close()
reactor.run()
"""
