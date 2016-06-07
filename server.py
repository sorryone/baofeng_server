# -*- coding: UTF-8 -*-
# Twisted server
# from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet.protocol import ServerFactory
from twisted.application import internet, service
# from twisted.internet import reactor
import pickle
import uuid
import sys
reload(sys)
sys.setdefaultencoding("utf-8")


def get_msg_data(buf):
    data_buf = buffer(buf)
    data_head = pickle.struct.unpack("3i", data_buf[:12])
    data_body = buf[12:]
    # print "unpack data = ", data_head
    return data_head, data_body


def set_msg_data(data, format_code, data_body=None):
    if not data:
        return data_body
    if not isinstance(data, (tuple, list)):
        raise TypeError
    buf = pickle.struct.pack(format_code, *data)
    # print "format_code=",format_code
    # print "pack buf = ", len(buf)
    # print "data=", data
    buf_data = None
    if data_body:
        buf_data = buf + data_body
    else:
        buf_data = buf

    return buf_data


def client_connect(client):
    print "New User Login:", client.getId()
    p_id = uuid.uuid1().get_hex()[:20]
    u_id = int(p_id[4:8], 16)
    msg_data = (8, 10002, u_id)
    buf = set_msg_data(msg_data, "3i")
    client.transport.write(buf)
    if client.factory.lobby:
        msg_data = (8, 10005, u_id)
        other_buf = set_msg_data(msg_data, "3i")
        for c in client.factory.lobby:
            c.transport.write(other_buf)

    client.factory.addLobby(client)


def client_login_game(client):
    print "New Player Login Game"
    msg_data = (4, 20002)
    buf = set_msg_data(msg_data, "2i")
    client.transport.write(buf)
    if client.factory.clients:
        msg_data = (4, 20005)
        other_buf = set_msg_data(msg_data, "2i")
        for c in client.factory.clients:
            c.transport.write(other_buf)

    client.factory.addClient(client)


class Game(LineOnlyReceiver):

    def dataReceived(self, buf):
        # print "===============> datarecevied, buf=", len(buf)
        if buf and len(buf) > 12:
            data_head, data_body = get_msg_data(buf)
            self.factory.sendAll(data_head, data_body, self)

    def lineReceived(self, buf):
        if buf and len(buf) > 12:
            data_head, data_body = get_msg_data(buf)
            self.factory.sendAll(data_head, data_body)

    def getId(self):
        return str(self.transport.getPeer())

    def connectionMade(self):
        client_connect(self)

    def connectionLost(self, reason):
        if self in self.factory.lobby:
            self.factory.delLobby(self)
        if self in self.factory.clients:
            self.factory.delClient(self)


class GameFactory(ServerFactory):
    protocol = Game

    def __init__(self, service):
        self.service = service
        self.master_uid = None
        self.clients = []
        self.lobby = []
        self.player = []
        self.msg = ''

    def getPlayerId(self):
        return len(self.player)

    def addLobby(self, client):
        self.lobby.append(client)

    def delLobby(self, client):
        self.lobby.remove(client)

    def addClient(self, client):
        self.clients.append(client)

    def delClient(self, client):
        self.clients.remove(client)

    def sendAll(self, data_head, data_body, client):
        if not isinstance(data_head, tuple):
            return
        # print "clinets num = ", len(self.clients)
        msg_len = data_head[0]
        # msg_num = data_head[1]
        msg_code = data_head[2]
        if msg_code == 20001:
            client_login_game(client)
        else:
            # print "msg_len=", msg_len
            # print "msg_num=", msg_num
            # print "msg_code=", msg_code
            buf = set_msg_data((msg_len-4, msg_code), "2i", data_body)
            for proto in self.clients:
                if proto != client:
                    proto.transport.write(buf)


# reactor.listenTCP(9001, GameFactory())
# reactor.run()

# configuration parameters
# iface = 'localhost'
# iface = "0.0.0.0"
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
