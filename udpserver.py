import json
import socket
import logging
from datetime import datetime
from multiprocessing import Process, Queue, freeze_support
import os


class UDPServer():
    def __init__(self, qr, qw):
        self.server = None
        self.tryCount = 1000
        self.speedMap = {}
        self.speedRes = {}
        self.address = None
        self.qr = qr
        self.qw = qw

    def init_server(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        address = ('0.0.0.0', 30000)
        while True:
            try:
                self.server.bind(address)
                print "UDP server bind to ", address
                break
            except Exception, e:
                print e
                address = (address[0], address[1] + 1)

    def start_server(self):
        p = Process(target=self.mainloop, args=())
        p.start()
        # p.join()
        return p

    def deal_parent_msg(self, msg):
        if msg['op'] == 'speed_test':
            if len(msg['slaves']) == 0:
                print "I'm the first"
            for remote in msg['slaves']:
                self.speed(remote)
            self.qw.put_nowait({'udp_address': "123456"})

    def deal_udp_msg(self, address, msg):
        func_dict = {
            'speed': self.deal_speed,
            'forward': self.deal_forward,
            'speedCallback': self.deal_speed_callback,
        }
        func = func_dict.get(msg['flag'])
        func(address, msg)

    def mainloop(self):
        self.init_server()
        print "UDP server start"
        # print "parent pid: ", str(os.getppid())
        print "pid: " + str(os.getpid())
        while True:
            if not self.qr.empty():
                msg = self.qr.get()
                self.deal_parent_msg(msg)
            else:
                data, address = self.server.recvfrom(4096)
                if not data:
                    print "something is wrong"
                    break
                print "receive ", data, "from", address
                self.deal_udp_msg(address, json.loads(data))

    def speed(self, address):
        tmp = str(datetime.now()).split(":")
        now = int(float(tmp[len(tmp) - 1]) * 1000000)
        self.speedMap[address] = now
        self.speedRes[address] = -1
        tmp = address.split(":")
        address = (tmp[0], int(tmp[1]))
        self.server.sendto("speed", address)

    def deal_speed_callback(self, address, data):
        tmp = str(datetime.now()).split(":")
        now = int(float(tmp[len(tmp) - 1]) * 1000000)
        time = (now - self.speedMap[str(address[0]+":"+str(address[1]))]) / 1000
        print "modifying ", str(address[0])+":"+str(address[1])
        self.speedRes[str(address[0])+":"+str(address[1])] = time

    def deal_speed(self, address, data):
        # tmp = address.split(":")
        # address = (tmp[0], tmp[1])
        self.server.sendto("speedCallback", address)

    def deal_forward(self, address, data):
        pass

    def __del__(self):
        self.server.close()

if __name__ == "__main__":
    server = UDPServer()
    server.start_server()
    print "server shutdown"
