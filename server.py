# -*- coding: UTF-8 -*-
# Twisted server
# from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet.protocol import ServerFactory
from twisted.application import internet, service
# from twisted.internet import reactor
import pickle
import uuid


def get_msg_data(buf):
    data_buf = buffer(buf)
    data_head = pickle.struct.unpack("3i", data_buf[:12])
    data_body = buf[12:]
    print "unpack data = ", data_head
    return data_head, data_body


def set_msg_data(data, format_code, data_body=None):
    if not data:
        return data_body
    if not isinstance(data, (tuple, list)):
        raise TypeError
    buf = pickle.struct.pack(format_code, *data)
    print "pack buf = ", buf
    buf_data = None
    if data_body:
        buf_data = buf + data_body
    else:
        buf_data = buf

    return buf_data


class Game(LineOnlyReceiver):

    def dataReceived(self, buf):
        print "===============> datarecevied, buf=", buf
        if buf and len(buf) > 12:
            data_head, data_body = get_msg_data(buf)
            self.factory.sendAll(data_head, data_body)

    def lineReceived(self, buf):
        print "===============> recdata =", buf
        if buf and len(buf) > 12:
            data_head, data_body = get_msg_data(buf)
            self.factory.sendAll(data_head, data_body)

    def getId(self):
        return str(self.transport.getPeer())

    def connectionMade(self):
        print "New User Login:", self.getId()
        p_id = uuid.uuid1().get_hex()[:20]
        u_id = "player_%s" % int(p_id[4:8], 16)
        msg_data = (10002, u_id)
        buf = set_msg_data(msg_data, "1is")
        self.transport.write(buf)
        self.factory.addClient(self)

    def connectionLost(self, reason):
        self.factory.delClient(self)


class GameFactory(ServerFactory):
    protocol = Game

    def __init__(self, service):
        self.service = service
        self.clients = []
        self.player = []
        self.msg = ''

    def getPlayerId(self):
        return len(self.player)

    def addClient(self, newclient):
        self.clients.append(newclient)

    def delClient(self, client):
        self.clients.remove(client)

    def sendAll(self, data_head, data_body):
        if not isinstance(data_head, tuple):
            return
        print "server_cur_client = ", self.clients
        # msg_len = data_head[0]
        msg_num = data_head[1]
        msg_code = data_head[2]
        if msg_num not in (10001, 10002):
            buf = set_msg_data((msg_code,), "1i", data_body)
            for proto in self.clients:
                proto.transport.write(buf)


# reactor.listenTCP(9001, GameFactory())
# reactor.run()

# configuration parameters
# iface = 'localhost'
#iface = "0.0.0.0"
# iface = "10.136.13.219"
iface = "::"
# iface = "123.118.195.147"
port = 9001

top_service = service.MultiService()
factory = GameFactory(top_service)
tcp_service = internet.TCPServer(port, factory, interface=iface)
tcp_service.setServiceParent(top_service)

application = service.Application("GameServer")
top_service.setServiceParent(application)
