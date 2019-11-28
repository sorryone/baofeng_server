# -*- coding: UTF-8 -*-
# Twisted server
# from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet.protocol import ServerFactory
from twisted.application import internet, service
from twisted.internet import reactor, endpoints
import pickle
import uuid
import sys
import time
import gevent
import importlib
#importlib.reload(sys)
importlib.reload(sys)
DEBUG = True
MAX_ROOM_NUM = 10
READY_TIME = 60
MAX_BUF_LEN = 8192


# 解析消息
def parse_package(client):
    temp_buf = client.factory.bufList
    # print("in package len = ", len(temp_buf))
    msg_len = pickle.struct.unpack("i", temp_buf[:4])[0]
    if msg_len > len(temp_buf) or len(temp_buf) < 16:
        print("None msg_len = ", msg_len)
        return None, None, None

    data_buf = client.factory.bufList[:msg_len]
    if len(data_buf) < 16:
        print(" error data_buf = ", data_buf)
    data_head = pickle.struct.unpack("4i", data_buf[:16])
    data_body = data_buf[16:]
    client.factory.bufList = client.factory.bufList[msg_len:]
    # print("end package len = ", len(client.factory.bufList))
    if DEBUG:
        pass
        # print("Recv Head = ", data_head)
    return data_head, data_body, data_buf


# 打包消息
def pack_msg(data, format_code, data_body=None):
    if not data:
        return data_body
    if not isinstance(data, (tuple, list)):
        raise TypeError
    buf = pickle.struct.pack(format_code, *data)
    if DEBUG:
        # print("Msg Head = ", format_code)
        # print("Msg len = ", len(buf))
        print("Msg Data = ", data)
    buf_data = None
    if data_body:
        buf_data = buf + data_body
    else:
        buf_data = buf

    return buf_data


# 用户连接 生成连接 生成u_id
def client_connect(client):
    if DEBUG:
        print(u"new Connect = ", client.getId())

    p_id = uuid.uuid1().get_hex()[:20]
    u_id = int(p_id[4:8], 16)
    client.factory.addClient(u_id, client)
    print("u_id ========", u_id)


# 用户登录 返回u_id
def client_login_game(client):
    print("New Player Login Game")
    u_id = client.factory.get_uid_by_client(client)
    msg_data = (16, 10002, u_id, -1)
    buf = pack_msg(msg_data, "4i")

    client.transport.write(buf)


# 创建新房间
def create_new_room(client):
    cur_room_id = client.factory.roomNum
    client.factory.rooms[client.factory.roomNum] = {
        "client_list": [],
        "master_uid": -1,
        "alive_num": {},
        "is_start": False,
        "ready_time": time.time()
    }
    client.factory.roomNum += 1
    return cur_room_id


# 检查房间 如果没有则创建 如果有则返回room_id
def check_room(client):
    if not client.factory.rooms:
        return create_new_room(client)

    for room_id, data in client.factory.rooms.iteritems():
        if len(data["client_list"]) < MAX_ROOM_NUM and not data["is_start"]:
            return room_id

    return create_new_room(client)


# 用户登录房间 并通知其他玩家有新玩家进入该房间
def client_in_room(client):
    room_id = check_room(client)
    u_id = client.factory.get_uid_by_client(client)
    print("room_id = ", room_id, " u_id = ", u_id, " roomList = ", client.factory.rooms)
    room_info = client.factory.rooms[room_id]

    if not room_info["client_list"]:
        room_info["master_uid"] = u_id
        room_info["ready_time"] = time.time()

    room_info["client_list"].append(client)
    room_info["alive_num"][u_id] = True

    c_time = int(time.time() - room_info["ready_time"])
    if room_info["is_start"]:
        c_time = 0

    print("shengyushijian = ", c_time)
    msg_data = (24, 20002, u_id, room_id, room_info["master_uid"], c_time)
    buf = pack_msg(msg_data, "6i")
    client.factory.set_room_id(u_id, room_id)
    for c in room_info["client_list"]:
        c.transport.write(buf)


# 主机开始游戏
def client_start_game(client):
    u_id = client.factory.get_uid_by_client(client)
    room_id = client.factory.get_room_id_by_u_id(u_id)
    room_info = client.factory.rooms.get(room_id, {})
    if not room_info:
        return

    room_info["is_start"] = True
    print("game Start")


# 有人死亡
def client_die(client, die_uid):
    room_id = client.factory.get_room_id_by_u_id(die_uid)
    room_info = client.factory.rooms.get(room_id, {})
    if not room_info:
        return

    room_info["alive_num"][die_uid] = False
    if room_info["alive_num"].values().count(True) == 1:
        for alive_uid, v in room_info["alive_num"].iteritems():
            if v:
                break

        # 游戏开始后房间剩下的最后一个人获得胜利
        msg_data = (20, 20010, alive_uid, room_id, alive_uid)
        buf = pack_msg(msg_data, "5i")
        for c in room_info["client_list"]:
            c.transport.write(buf)
    else:
        alive_num = room_info["alive_num"].values().count(True)
        msg_data = (24, 20009, die_uid, room_id, room_info["master_uid"], alive_num)
        buf = pack_msg(msg_data, "6i")
        for c in room_info["client_list"]:
            c.transport.write(buf)

# 用户退出房间
def client_out_room(client):
    u_id = client.factory.get_uid_by_client(client)
    room_id = client.factory.get_room_id_by_u_id(u_id)
    room_info = client.factory.rooms.get(room_id, {})
    if not room_info:
        return

    u_id = client.factory.get_uid_by_client(client)
    client.factory.set_room_id(u_id, -1)
    clear_room = False
    try:
        room_info["client_list"].remove(client)
        room_info["alive_num"].pop(u_id)
        if room_info["master_uid"] == u_id:
            if not room_info["client_list"]:
                room_info["master_uid"] = -1
                # 关闭该房间
                client.factory.rooms.pop(room_id)
                clear_room = True
            else:
                room_info["master_uid"] = client.factory.get_uid_by_client(
                    room_info["client_list"][0])

        # if room_info["alive_num"] >= 1:
        #    room_info["alive_num"] -= 1

    except AttributeError:
        print("Error, room_info.remove(client)")
        pass

    # 如果房间被关闭 则部需要发送数据
    if clear_room:
        return

    msg_data = (20, 20004, u_id, room_id, room_info["master_uid"])
    buf = pack_msg(msg_data, "5i")
    for c in room_info["client_list"]:
        c.transport.write(buf)


# 用户离开游戏
def client_logout_game(client):
    if DEBUG:
        print("用户退出游戏")
    client_out_room(client)
    client.factory.delClient(client)
    print("RoomList = ", client.factory.rooms)


class Game(LineOnlyReceiver):

    def dataReceived(self, buf):
        if buf and len(buf) >= 16:
            gevent.spawn(self.put_buf, buf).join(),
            gevent.spawn(self.worker),

    def put_buf(self, buf):
        self.factory.bufList += buf
        if len(self.factory.bufList) > MAX_BUF_LEN:
            print("Msg MAX Len", len(self.factory.bufList))
        # gevent.sleep(0)

    def worker(self):
        while len(self.factory.bufList) >= 16:
            data_head, data_body, temp_buf = parse_package(self)
            if not data_head:
                break
            self.factory.msg_process(data_head, data_body, self, temp_buf)
        # gevent.sleep(0)

    def lineReceived(self, buf):
        pass

    def getId(self):
        return str(self.transport.getPeer())

    def connectionMade(self):
        client_connect(self)

    def connectionLost(self, reason):
        client_logout_game(self)


class GameFactory(ServerFactory):
    protocol = Game

    def __init__(self, service):
        self.service = service
        self.bufList = memoryview("")
        self.roomNum = 0
        # 客户端列表
        self.clients = {}
        # 对战列表
        self.rooms = {}
        self.msg = ''

    def addClient(self, u_id, client):
        self.clients[u_id] = {
            "client": client,
            "room_id": -1,
            }

    def set_room_id(self, u_id, room_id):
        self.clients[u_id]["room_id"] = room_id

    def delClient(self, u_id):
        if u_id in self.clients:
            self.clients.pop(u_id)

    def get_uid_by_client(self, client):
        for k, v in self.clients.iteritems():
            if v["client"] is client:
                return k

    def get_room_id_by_client(self, client):
        for k, v in self.clients.iteritems():
            if v["client"] is client:
                return v["room_id"]

    def get_room_id_by_u_id(self, u_id):
        return self.clients[u_id]["room_id"]

    def msg_process(self, data_head, data_body, client, buf):
        msg_len = int(data_head[0])
        if msg_len < len(data_body) + 16:
            print("error data_head = ", data_head, "buf len= ", len(data_body))
        msg_code = str(data_head[1])
        msg_uid = int(data_head[2])
        msg_room_id = int(data_head[3])

        # 大厅消息
        if msg_code[:1] == "1":
            if msg_code == "10001" and msg_uid == -1:
                client_login_game(client)
            elif msg_code == "10003":
                client_logout_game(client)

        # 房间消息
        elif msg_code[:1] == "2":
            if msg_code == "20001" and msg_room_id == -1:
                client_in_room(client)
            elif msg_code == "20003":
                client_out_room(client)
            elif msg_code == "20005":
                client_start_game(client)
            else:
                if msg_code == "20033":
                    _, target, is_k = pickle.struct.unpack("2i1?", buf[16:25])
                    print("player die id = ", target, " kill = ", is_k)
                    if is_k:
                        client_die(client, target)
                self.sendAll(client, buf)

    def sendAll(self, client, buf):
        u_id = client.factory.get_uid_by_client(client)
        room_id = client.factory.get_room_id_by_u_id(u_id)
        if room_id not in self.rooms:
            return
        for v in self.rooms[room_id]["client_list"]:
            if v != client:
                v.transport.write(buf)


# endpoints.serverFromString(reactor, "tcp:1234").listen(GameFactory())
top_service = service.MultiService()
reactor.listenTCP(1234, GameFactory(top_service))
reactor.run()

# configuration parameters
"""
iface = "0.0.0.0"
port = 1234
top_service = service.MultiService()
factory = GameFactory(top_service)
tcp_service = internet.TCPServer(port, factory, interface=iface)
tcp_service.setServiceParent(top_service)
application = service.Application("GameServerAPP")
top_service.setServiceParent(application)
"""
# top_service.setServicePry = GameFactory(application)
