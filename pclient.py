# -*- encoding:utf-8 -*-
import socket
import struct
import multiprocessing
import time


def connToServer(pid):
    print("===========pid", pid)
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect(("127.0.0.1", 9527))
    d = struct.pack("3i3h20s", 38, 1001, pid, 0, 1, 20, b'test')
    conn.send(d)
    dd = struct.pack("3ih?", 15, 1012, pid, 1, True)
    conn.send(dd)
    while True:
        time.sleep(1)


def main():
    jobs = []
    times = 398
    for i in range(0, times):
        p = multiprocessing.Process(target=connToServer, args=(2000 + i,))
        jobs.append(p)
        p.start()


if __name__ == "__main__":
    main()
