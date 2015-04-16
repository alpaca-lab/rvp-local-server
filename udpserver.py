import json
import socket
import logging
from datetime import datetime
from multiprocessing import Process
import os


class UDPServer():
    def __init__(self):
        self.server = None
        self.tryCount = 1000
        self.speedMap = {}
        self.speedRes = {}

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

    def run(self):
        logging.info("UDP server start")
        logging.info("parent pid: " + str(os.getppid()))
        logging.info("pid: " + str(os.getpid()))
        while True:
            data, address = self.server.recvfrom(4096)
            if not data:
                print "something is wrong"
                break
            print "receive ", data, "from", address
            func_dict = {
                'speed': self.deal_speed,
                'forward': self.deal_forward,
                'speedCallback': self.deal_speed_callback,
            }

            func = func_dict.get(json.loads(data)['flag'])
            func(address, data)

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
    server.init_server()
    p = Process(target=server.run, args=())
    print "server shutdown"