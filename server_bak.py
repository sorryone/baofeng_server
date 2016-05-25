# -*- coding: UTF-8 -*-
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet import reactor
import random
import string

class Game(LineOnlyReceiver):

    def dataReceived(self, data):
        print "datarecevied, data=", data
        print "id = ", self.getId()
        self.factory.sendAll("%s" % (data))

    def lineReceived(self, data):
        print "===============> recdata = %s" % data
        self.factory.sendAll("%s" % (data))
    def getId(self):
        return str(self.transport.getPeer())

    def connectionMade(self):
        print "New User Login:", self.getId()
        self.transport.write("welcome to my game")
        self.factory.addClient(self)

    def connectionLost(self, reason):
        self.factory.delClient(self)

class GameFactory(Factory):
    protocol = Game
    def __init__(self):
        self.clients = []
        self.player = []
        self.msg = ''
        self.x = range(100, 700)
        self.y = range(100, 700)

    def getPlayerId(self):
        return len(self.player)

    def addClient(self, newclient):
        self.clients.append(newclient)

    def delClient(self, client):
        self.clients.remove(client)

    def sendAll(self, data):
        if data.find('<policy-file-request/>')!=-1:
            proto.transport.write('<cross-domain-policy><allow-access-from domain="127.0.0.1" to-ports="*"/></cross-domain-policy>\0')
        else:
            print "clients = ", self.clients
            arr = data.split(':')
            prefix = arr[0]
            content = arr[1]
            if prefix.find('player') != -1:
                newPlayer = [content,str(random.randrange(200,
                             600)),str(random.randrange(150,350)),
                             str(random.randrange(1,5))]

                self.player.append(newPlayer)
                self.msg = ' player '+content+ "in game"
                # guangbo
                temp = []
                playerData = ':::'
                for pos in self.player:
                    temp.append(string.join(pos, '---'))
                playerData = playerData+string.join(temp,'***')
                for proto in self.clients:
                    proto.transport.write(' [SYS] ' +self.msg+'\n')
                    proto.transport.write(playerData)

            elif prefix.find('pos')!=-1:
                playerName, x, y = content.split('---')
                i = 0
                for p in self.player:
                    if p[0] == playerName:
                        p[1] = x
                        p[2] = y

                for proto in self.clients:
                    proto.transport.write(data)

            else:
                print 3333
                self.msg = data
                for proto in self.clients:
                    proto.transport.write(self.msg+'\n')


reactor.listenTCP(9001, GameFactory())
reactor.run()

