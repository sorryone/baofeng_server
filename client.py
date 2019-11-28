# -*- coding: UTF-8 -*-
from twisted.internet.protocol import ClientFactory, Protocol
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
from twisted.internet import defer
import sys

class Sender(Protocol):
    def sendCommand(self, command):
        print "invio", command
        self.transport.write(command)

    def senderReceived(self, data):
        print "DATA", data
        self.factory.sender_finished(data)


PORT = 1234
HOST = 'localhost'

class PoetryClientFactory(ClientFactory):
    protocol = Sender
    def __init__(self, deferred):
        self.deferred = deferred

    def sender_finished(self, data):
        if self.deferred is not None:
            d, self.deferred = self.deferred, None
            d.callback(data)
    def clientConnectionFailed(self, connector, reason):
        if self.deferred is not None:
            d, self.deferred = self.deferred, None
            d.errback(reason)

def get_poetry():
    d = defer.Deferred()
    from twisted.internet import reactor
    c = PoetryClientFactory(d)
    reactor.connectTCP(HOST, PORT, c)
    return d

if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in \
            ['stop', 'next_call','force']:

        sys.stderr.write('Usage: %s: {stop|next_call|force}\n' %
                         sys.argv[0])
        sys.exit(1)

    def got_data(data):
        print "got_data ", data

    def data_failed(err):
        print >>sys.stderr, 'data failed:', err

    d = get_poetry()
    d.addCallbacks(got_data, data_failed)
    reactor.run()
