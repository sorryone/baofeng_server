#!/usr/bin/python3
# -*- coding: utf-8 -*-
from socket import *
from threading import Thread

port_list = []
def portScanner(host, port):
    try:
        s = socket(AF_INET, SOCK_STREAM)
        s.connect((host, port))
        print("port is Open = ", port)
        s.close()
        prot_list.append(port)
    except Exception:
        pass
        # print("port is Close = ", port)

def main():
    setdefaulttimeout(1)
    ip = "89.248.174.144"
    # ip = "127.0.0.1"
    for p in range(1, 65535):
        t = Thread(target=portScanner, args=(ip, p))

        t.start()

    print("scan is Done", port_list)

if __name__ == '__main__':
    main()
