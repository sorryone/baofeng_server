# -*- coding: UTF-8 -*-
from twisted.internet.protocol import ClientCreator, Protocol
from twisted.internet import reactor
import sys
import random
import pickle


def get_msg_data(buf):
    buf_data = buffer(buf)
    data = pickle.struct.unpack("1i", buf_data[:4])
    print "unpack data = ", data
    return data


def set_msg_data(data, format_code):
    if not isinstance(data, tuple):
        raise TypeError
    buf = pickle.struct.pack(format_code, *data)
    print "pack buf = ", buf
    return buf


class Sender(Protocol):
    def sendCommand(self, command):
        command = command.strip()
        if command == "login":
            game_data = {
                "msg": "new player login game"
            }
            data = (len(game_data["msg"]), random.randint(0, 10),
                    10001, game_data["msg"])
            buf = set_msg_data(data, "3i%ss" % len(game_data["msg"]))
            self.transport.write(buf)
        elif command == "run":
            data = (20, random.randint(0, 10),
                    10003, random.randint(0, 100), random.randint(0, 100),
                    random.randint(0, 100))
            buf = set_msg_data(data, "3i3f")
            self.transport.write(buf)
        elif command == "stop":
            data = (12, random.randint(0, 10), 10003)
            buf = set_msg_data(data, "3i")
            self.transport.write(buf)

    def dataReceived(self, buf):
        get_msg_data(buf)


PORT = 9001
HOST = '123.59.110.191'


def sendCommand(command):
    def test(d):
        print "Invio ->", command
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
