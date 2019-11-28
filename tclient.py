# -*- encoding:utf-8 -*-
import socket
import struct
import threading


def connToServer(pid):
    print("===========pid", pid)
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect(("127.0.0.1", 9527))
    d = struct.pack("3i3h20s", 38, 1001, pid, 0, 1, 20, b'test')
    conn.send(d)
    dd = struct.pack("3ih?", 15, 1012, pid, 1, True)
    conn.send(dd)


def main():
    threads = []
    times = 398
    for i in range(0, times):
        t = threading.Thread(target=connToServer(2000 + i))
        threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join()


if __name__ == "__main__":
    main()
