# -*- coding: UTF-8 -*-
from twisted.internet.protocol import ClientCreator, Protocol
from twisted.internet import reactor
import sys
import random
import pickle

class Sender(Protocol):
    def sendCommand(self, command):
        #command = command.strip()
        #self.transport.write(buf)
        pass

    def dataReceived(self, buf):
        print("buf =====", len(buf))
        # get_msg_data(buf)


PORT = 1234
HOST = '127.0.0.1'


def sendCommand(command):
    def test(d):
        d.sendCommand(command)

    c = ClientCreator(reactor, Sender)
    c.connectTCP(HOST, PORT).addCallback(test)


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in \
            ['run', 'stop', 'login']:
        sys.stderr.write('Usage: %s: {run|stop|login}\n'
                         % sys.argv[0])

        sys.exit(1)

    sendCommand(sys.argv[1]+'\n')
    reactor.run()
