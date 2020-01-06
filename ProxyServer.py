from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import ServerFactory
from twisted.application import strports, service
from twisted.internet import reactor
import struct
# import uuid
# import sys
# import time
import gevent
# import importlib
# MAX_BUF_COUNT = 80
MAX_BUF_LEN = 8192
MIN_HEAD = 12
MIN_LEN = 4
STR_LEN = 20

# 注意内存对其问题 从大到小 int short bool 不对其 从小到大则对其
Msg_Data = {
    1001: {
        "format_code": "3h%ss" % STR_LEN,
        "attr": ["user_type", "school_id", "user_name_len", "user_name"],
    },
    1002: {
        # 用户再次登录 如果该用户在房间里 返回room_id
        "format_code": "h",
        "attr": ["room_id"],
    },
    1100: {
        # 学生信息
        "format_code": "i2h%ss" % STR_LEN,
        "attr": ["user_id", "user_type", "user_name_len", "user_name"],
    },

    1003: {
        # 客户端请求房间列表
        "format_code": "",
        "attr": [],
    },

    1004: {
        # 服务器返回房间列表(多条1011)
        "format_code": "h",
        "attr": ["count"],
    },

    1005: {
        "format_code": "",
        "attr": [],
    },

    1010: {
        # 创建房间C-S
        "format_code": "ih%ssh%ss2h?" % (STR_LEN, STR_LEN),
        "attr": ["owner_id", "owner_name_len", "owner_name",
                 "course_name_len", "course_name",
                 "subject_id", "course_id", "is_public"],
    },
    1011: {
        # 创建房间成功返回值S-C
        "format_code": "ih%ssh%ss4h?" % (STR_LEN, STR_LEN),
        "attr": ["owner_id", "owner_name_len", "owner_name",
                 "course_name_len", "course_name",
                 "subject_id", "course_id", "room_id", "onlineCt", "is_public"]
    },
    1012: {
        # 用户进入房间C-S
        "format_code": "h?",
        "attr": ["room_id", "is_enter"],
    },
    1013: {
        # 发给大厅的人更新房间人数 S-C
        "format_code": "2h",
        "attr": ["room_id", "onlineCt"],
    },
    1014: {
        # 发给房主用户登录 S-C
        "format_code": "2h%ss?" % STR_LEN,
        "attr": ["user_type", "user_name_len", "user_name", "is_enter"],
    },
    1015: {
        # 发送删除房间 S-C
        "format_code": "h",
        "attr": ["room_id"],
    },
    1016: {
        # 发送学生列表给所有老师及管理员 S-C
        "format_code": "h",
        "attr": ["count"],
    },
    1017: {
        # 通知房间里的所有学生初始化
        "format_code": "",
        "attr": [],
    },
    1018: {
        # 通知房间里的人新房主的id
        "format_code": "ih",
        "attr": ["owner_id", "room_id"],
    },
    2001: {
        "format_code": "",
        "attr": [],
    },
    2002: {
        "format_code": "",
        "attr": [],
    },
    2003: {
        "format_code": "",
        "attr": [],
    },
    2004: {
        # 手柄射线
        "format_code": "",
        "attr": [],
    },
    2005: {
        # 语音
        "format_code": "",
        "attr": [],
    },
}


def unpack_head(factory, buf):
    if len(factory.NoBufList) > 0:
        buf = factory.NoBufList + buf
        # print("!!!缓存长度 =", len(factory.NoBufList), " 当前长度 =", len(buf))
        factory.NoBufList.clear()
        # print("unpack buf = ", buf)

    if len(buf) < MIN_HEAD:
        print("Error=========== buf len < 12")
        return False, buf

    msg_len = struct.unpack("i", buf[:4])[0]
    if msg_len > MAX_BUF_LEN:
        print("Error==========msg_len = ", msg_len, " buf_len =", len(buf))
        print("Error==NoBufList = ", factory.NoBufList,  "top 20 = ", buf[:20])
        return False, buf

    msg_code = struct.unpack("i", buf[4:8])[0]
    if msg_code not in Msg_Data:
        print("Error==========msg_code =", msg_code)
        print("Error==NoBufList = ", factory.NoBufList,  "top 20 = ", buf[:20])
        return False, buf

    # print("msgLen = ", len(buf))
    # print("ok True")
    return True, buf


# 解析消息
def unpack_msg(factory):
    temp_buf = factory.bufList
    if len(temp_buf) < 4:
        factory.NoBufList = temp_buf[:]
        print("消息头长度不够 = len = ", len(temp_buf), " data = ",
              temp_buf)

        factory.bufList.clear()
        print("消息头长度不够 =  after data = ", factory.NoBufList)
        return None, None

    msg_len = struct.unpack("i", temp_buf[:4])[0]
    data_buf = temp_buf[:msg_len]
    # print("消息长度 = ", msg_len, "数据长度 = ", len(temp_buf))
    # 消息长度不够
    if len(data_buf) != msg_len or len(data_buf) < 12:
        factory.NoBufList = data_buf
        # print("!!!!!, 长度不够 =", len(data_buf), "==需要  = ", msg_len)
        factory.bufList.clear()
        return None, None

    data_head = struct.unpack("3i", data_buf[:MIN_HEAD])
    factory.bufList = factory.bufList[msg_len:]
    return data_head, data_buf


def unpack_body(msg_len, msg_code, data_buf):
    body_format = Msg_Data.get(msg_code, None)
    if body_format is None:
        return data_buf

    pack_data = struct.unpack(body_format["format_code"], data_buf[MIN_HEAD:])
    data = {}
    for index, value in enumerate(pack_data):
        data[body_format["attr"][index]] = value

    return data


def processingLogic(client, factory, data_head, data_buf):
    msg_len = int(data_head[0])
    msg_code = int(data_head[1])
    user_id = int(data_head[2])
    # print("msg_len = ", msg_len, "msg_code= ", msg_code, "user_id ", user_id)
    if msg_code == 1001:
        # 客户端登录请求
        data_body = unpack_body(msg_len, msg_code, data_buf)
        print("=============>", data_body)
        par_client = None
        if user_id in factory.users:
            if client != factory.users[user_id]["client"]:
                par_client = factory.users[user_id]["client"]
                print("re_cliet===nbefore===", client, "==after=", par_client)

        factory.users[user_id] = {
            "client": client,
            "user_type": data_body["user_type"],
            "school_id": data_body["school_id"],
            "user_name_len": data_body["user_name_len"],
            "user_name": data_body["user_name"]
        }

        room_id = factory.GetRoomForUser(user_id)
        if room_id != -1:
            # 如果用户上次掉线 并且在房间里 更新房间尸体的信息
            par_client = factory.rooms[room_id]["users"][user_id]["client"]
            if par_client == client:
                par_client = None
            print("before =", par_client, "===<>after = ", client)
            factory.rooms[room_id]["users"][user_id] = factory.users[user_id]
            factory.users.pop(user_id)

        params = {
            "room_id": room_id,
        }
        data = pack_msg(1002, dict_d=params, uid=user_id)
        client.transport.write(data)

        # 发给上次的client 登出请求
        if par_client is not None:
            d = pack_msg(1005, uid=user_id)
            par_client.transport.write(d)

        print("login === users = ", factory.users.keys(), "user_id=", user_id)
        # print("login ==== user.client = ", factory.users[user_id]["client"])
    elif msg_code == 1003:
        # 客户端请求房间列表
        # 返回1004
        user = None
        if user_id in factory.users:
            user = factory.users[user_id]
        else:
            room_id = factory.GetRoomForUser(user_id)
            if room_id == -1:
                return
            user = factory.rooms[room_id]["users"][user_id]
        if user is None:
            return

        school_id = user["school_id"]
        params = []
        for k, v in factory.rooms.items():
            owner_id, owner = factory.GetOwnerClient(k)
            if v["is_public"] or owner["school_id"] == school_id:
                params.append(v)

        data = pack_msg_list(1004, 1011, dict_d=params, uid=user_id)
        print("code = 1004 user_id = ", user_id, " client = ", user["client"])
        user["client"].transport.write(data)

    elif msg_code == 1010:
        if user_id not in factory.users:
            return
        user_type = factory.users[user_id]["user_type"]
        # 客户端发送创建房间请求
        data_body = unpack_body(msg_len, msg_code, data_buf)
        # print("=============>", data_body)

        # 普通老师只能建普通课房间 管理员可以创建全国公开课房间
        if data_body["is_public"]:
            if user_type != 3:
                return
        else:
            if user_type != 0:
                return
        is_has = {k for k, v in factory.rooms.items()
                  if data_body["owner_id"] in v}

        if is_has:
            # 如果房间已经被创建 返回
            return

        # 创建一个房间
        room_id = factory.GetRoomId()
        factory.rooms[room_id] = data_body
        factory.rooms[room_id]["users"] = {}
        factory.rooms[room_id]["users"][user_id] = factory.users[user_id]
        print("========rooms = ", factory.rooms.keys())

        data_body["room_id"] = room_id
        data_body["onlineCt"] = factory.GetRoomNums(room_id)
        data = pack_msg(1011, dict_d=data_body)
        # 发送消息给大厅的用户 包含自己
        school_id = factory.users[user_id]["school_id"]
        is_public = factory.GetPublicRoom(room_id)
        users = factory.GetSchoolUser(school_id, is_public)
        for k, v in users.items():
            v["client"].transport.write(data)

        # 把这个用户从大厅移动到房间
        factory.users.pop(user_id)

    elif msg_code == 1012:
        # 用户进入/ 退出房间C-S
        data_body = unpack_body(msg_len, msg_code, data_buf)
        print("================>", data_body)

        room_id = data_body["room_id"]
        if room_id not in factory.rooms:
            return
        # 房间拥有者
        owner_id, owner = factory.GetOwnerClient(room_id)
        is_enter = data_body["is_enter"]
        is_public = factory.GetPublicRoom(room_id)
        # 房间拥有者关闭房间
        if owner_id == user_id:
            if is_enter:
                # 通知房间所有用户老师重连
                data = pack_msg(1017, uid=user_id)
                for k, v in factory.rooms[room_id]["users"].items():
                    v["client"].transport.write(data)
            else:
                # 通知大厅用户房间删除
                SendLogout(factory, room_id, user_id, is_public)
                return
        else:
            user = factory.EnterRoom(room_id, user_id, is_enter)
            if not user:
                return
            school_id = user["school_id"]
            print("=======rooms info = ", factory.rooms.keys())
            # 发送广播数据给大厅的用户
            data_params = {
                "room_id": room_id,
                "onlineCt": factory.GetRoomNums(room_id),
            }
            data = pack_msg(1013, dict_d=data_params, uid=user_id)

            # 发送消息给大厅的用户
            users = factory.GetSchoolUser(school_id, is_public)
            for k, v in users.items():
                v["client"].transport.write(data)

            # 发数据给房间的创建者有人进入
            if is_enter:
                user = factory.rooms[room_id]["users"][user_id]
            else:
                user = factory.users[user_id]
            data_params = {
                "user_type": user["user_type"],
                "user_name_len": user["user_name_len"],
                "user_name": user["user_name"],
                "is_enter": is_enter,
            }
            data = pack_msg(1014, dict_d=data_params, uid=user_id)
            # 发送进入用户数据给所有老师及管理员
            for k, udata in factory.rooms[room_id]["users"].items():
                if udata["user_type"] in (0, 3):
                    udata["client"].transport.write(data)

        if is_enter:
            # 发送房间信息给老师
            SendRoomUserList(room_id, user_id)

    elif msg_code == 1018:
        # 更换房主并推送给房间所有人
        data_body = unpack_body(msg_len, msg_code, data_buf)
        room_id = data_body.get("room_id", 0)
        owner = factory.SetOwnerUser(
                     room_id, user_id, data_body.get("owner_id", 0))

        if owner is None:
            return

        school_id = owner["school_id"]
        is_public = factory.GetPublicRoom(room_id)
        users = factory.GetSchoolUser(school_id, is_public)
        # 推送大厅用户
        for k, v in users.items():
            v["client"].transport.write(data_buf)

        # 推送房间所有人
        for k, v in factory.rooms[room_id]["users"].items():
            v["client"].transport.write(data_buf)

    elif msg_code == 2001:
        # 转发消息给房间内的所有人
        room_id = factory.GetRoomForUser(user_id)
        if room_id == -1:
            return

        # s = struct.unpack("h", data_buf[MIN_HEAD:MIN_HEAD+2])
        # if s[0] == 0:
            # return

        room_info = factory.rooms[room_id]
        for k, v in room_info["users"].items():
            if k != user_id:
                v["client"].transport.write(data_buf)
                # print("client uid = ", k, "buf =", data_buf)

    elif msg_code == 2004 or msg_code == 2005:
        # 转发手柄射线
        room_id = factory.GetRoomForUser(user_id)
        if room_id == -1:
            return

        room_info = factory.rooms[room_id]
        for k, v in room_info["users"].items():
            if k != user_id:
                v["client"].transport.write(data_buf)

    elif msg_code == 2002:
        # 发送消息给房主
        room_id = factory.GetRoomForUser(user_id)
        if room_id == -1:
            return

        _, owner = factory.GetOwnerClient(room_id)
        owner['client'].transport.write(data_buf)

    elif msg_code == 2003:
        # 发消息给某个用户
        user = factory.users.get(user_id, None)
        if user is None:
            room_id = factory.GetRoomForUser(user_id)
            if room_id == -1:
                return

            user = factory.rooms[room_id]["users"].get(user_id, None)

        if user is None:
            return

        user["client"].transport.write(data_buf)

    # print("send Finish, factory.bufList = ", len(factory.bufList))


# 发送房间用户列表给user_id 该用户必须是老师及管理员
def SendRoomUserList(room_id, user_id):
    params = []
    for uid, udata in factory.rooms[room_id]["users"].items():
        params.append({
                        "user_id": uid,
                        "user_type": udata["user_type"],
                        "user_name_len": udata["user_name_len"],
                        "user_name": udata["user_name"],
                    })

    data = pack_msg_list(1016, 1100, dict_d=params, uid=user_id)
    user = factory.rooms[room_id]["users"][user_id]
    if user["user_type"] in (0, 3):
        user["client"].transport.write(data)


def SendLogout(factory, room_id, user_id, is_public, is_remove=False):
    # 通知大厅用户房间删除
    factory.CloseRoom(room_id)
    # 通知房间用户退出 通知大厅用户房间删除
    data_params = {"room_id": room_id}
    school_id = factory.users[user_id]["school_id"]
    data = pack_msg(1015, dict_d=data_params, uid=user_id)
    if is_remove:
        factory.users.pop(user_id)
    print("logout = ", factory.users.keys(), " isremove=", is_remove)
    users = factory.GetSchoolUser(school_id, is_public)
    for k, v in users.items():
        print("code = 1015 user_id = ", k, " client = ", v["client"])
        v["client"].transport.write(data)


def SendPlayerLogout():
    pass


# 打包消息
def pack_msg(code, values=(), format_params=None, dict_d={}, uid=-1):
    if not isinstance(values, (tuple, list)):
        raise TypeError
    buf = ""
    if code in Msg_Data.keys():
        # print("in Msg_Data code = ", code)
        format_code = Msg_Data[code]["format_code"]
        data = []
        for attr in Msg_Data[code]["attr"]:
            if attr in dict_d:
                data.append(dict_d[attr])
        # print("dict_d = ", dict_d)
        print("code_attr = ", Msg_Data[code]["attr"], "code = ", code)
        # print("pack_MsgData = ", data, "farmat = ", format_code)
        buf = struct.pack(format_code, *data)
        lens = struct.calcsize(format_code) + MIN_HEAD
        head_buf = struct.pack("3i", lens, code, uid)
        buf = head_buf + buf
    else:
        print(" in No  code = ", code)
        if format_params is not None:
            buf = struct.pack(format_params, *values)
            lens = struct.calcsize(format_params) + MIN_HEAD
            head_buf = struct.pack("3i", lens, code, uid)
            buf = head_buf + buf
        else:
            buf = struct.pack("3i", MIN_HEAD, code, uid)

    # print("return buf = ", buf, "==========buf len = ", len(buf))
    # print("======return buf len = ", len(buf))
    return buf


# 打包数组
def pack_msg_list(code, sub_code, dict_d=[], uid=-1):
    sub_format_code = Msg_Data[sub_code]["format_code"]

    sub_body_bufs = bytes()
    for one_data in dict_d:
        data = []
        for attr in Msg_Data[sub_code]["attr"]:
            if attr in one_data:
                data.append(one_data[attr])

        sub_body = struct.pack(sub_format_code, *data)
        sub_body_bufs += sub_body

    # sub_lens = struct.calcsize(sub_format_code * len(dict_d))
    sub_lens = len(sub_body_bufs)
    print("sub_lens = ", sub_format_code * len(dict_d), " lens=", sub_lens)
    format_code = Msg_Data[code]["format_code"]
    lens = struct.calcsize(format_code) + sub_lens + MIN_HEAD
    head_buf = struct.pack("3i", lens, code, uid)
    # 这里目前数组只有一个长度
    body_buf = struct.pack(format_code, len(dict_d))
    buf = head_buf + body_buf + sub_body_bufs

    # print("return buf = ", buf, "==========buf len = ", len(buf))
    return buf


class Game(LineReceiver):
    def dataReceived(self, buf):
        rc, buf = unpack_head(factory, buf)
        if not rc:
            return

        # gevent.spawn(self.put_buf, buf).join()
        self.put_buf(buf)
        gevent.spawn(self.worker())
        # self.put_buf(buf)
        # self.worker()

    def put_buf(self, buf):
        # print("====== recvdata buf.len = ", len(buf))
        factory.bufList += buf
        if len(factory.bufList) > MAX_BUF_LEN:
            print("Warning!!!! Msg MAX Len", len(self.factory.bufList))

    def worker(self):
        while len(factory.bufList) > 0:
            data_head, data_buf = unpack_msg(factory)
            if data_head is None:
                break
            processingLogic(self, factory, data_head, data_buf)

    def connectionMade(self):
        # data = pack_msg(9999)
        # data = pack_msg(9999, format_params="ih%ssh?" % STR_LEN,
        #                values=(999, 12, b"oqwiodjqiow", 7, True))
        # self.transport.write(data)
        ip = self.transport.getPeer().host
        print("=============== connect client ip = ", ip)

    def connectionLost(self, reason):
        ip = self.transport.getPeer().host
        print("===========user login out!!! client = ", self, " ip=", ip)
        for room_id, room_info in factory.rooms.items():
            is_public = factory.GetPublicRoom(room_id)
            owner_id, owner = factory.GetOwnerClient(room_id)
            if owner["client"] == self:
                print("=======use login out owner client = ", owner["client"])
                SendLogout(factory, room_id, owner_id, is_public, True)
                break

        user_id = -1
        for k, user_info in factory.users.items():
            if user_info["client"] == self:
                user_id = k

        if user_id != -1:
            factory.users.pop(user_id)
        print("===========user login out!!! users = ", factory.users.keys())

    def lineReceived(self, buf):
        pass


class GameFactory(ServerFactory):
    protocol = Game

    def __init__(self):
        self.bufList = bytearray()
        self.NoBufList = bytearray()
        self.users = {}
        self.rooms = {}
        self.room_id = 0

    def GetRoomId(self):
        self.room_id += 1
        return self.room_id

    def GetRoomNums(self, room_id):
        if room_id not in self.rooms:
            return 0
        return len(self.rooms[room_id]["users"])

    # 用户进入/退出房间
    def EnterRoom(self, room_id, user_id, is_enter):
        if is_enter:
            if user_id not in self.users:
                return {}
            self.rooms[room_id]["users"][user_id] = self.users[user_id]
            return self.users.pop(user_id)
        else:
            if user_id not in self.rooms[room_id]["users"]:
                return
            self.users[user_id] = self.rooms[room_id]["users"][user_id]

            user_info = self.rooms[room_id]["users"].pop(user_id)
            return user_info

    # 老师关闭房间
    def CloseRoom(self, room_id):
        users = self.rooms[room_id]["users"]
        self.users.update(users)
        self.rooms.pop(room_id)
        print("========= Close room = ", self.rooms.keys())
        return users

    def GetOwnerClient(self, room_id):
        if room_id not in self.rooms:
            return {}

        user_id = self.rooms[room_id]["owner_id"]
        return user_id, self.rooms[room_id]["users"][user_id]

    def SetOwnerUser(self, room_id, old_id, set_id):
        if room_id not in self.rooms:
            return None

        # if old_id != self.rooms[room_id]["owner_id"]:
        #    return None

        if set_id not in self.rooms[room_id]["users"]:
            return None

        self.rooms[room_id]["owner_id"] = set_id
        return self.rooms[room_id]["users"][set_id]

    def GetSchoolUser(self, school_id, is_public):
        if is_public:
            return self.users

        user_list = {}
        for k, v in self.users.items():
            if v["school_id"] == school_id:
                user_list[k] = v
        return user_list

    def GetPublicRoom(self, room_id):
        return self.rooms[room_id]["is_public"]

    # 查找用户id是否在房间
    def GetRoomForUser(self, user_id):
        room_id = -1
        for rid, rdata in self.rooms.items():
            for uid in rdata["users"].keys():
                if uid == user_id:
                    room_id = rid
                    break

        return room_id


application = service.Application('ProxyServer')
factory = GameFactory()
strports.service("tcp:9527", factory, reactor=reactor).setServiceParent(
    service.IServiceCollection(application))
