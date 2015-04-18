# coding: utf-8
import json
import time
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
        address = ('192.168.1.204', 30000)
        while True:
            try:
                self.server.bind(address)
                print "UDP server bind to ", address
                self.address = address
                break
            except Exception, e:
                print e
                address = (address[0], address[1] + 1)

    def deal_parent_msg(self,):
        msg = self.msg_from_parent()
        print 'receive', msg, ' from parent'
        if msg is None:
            return
        if msg['op'] == 'speed_test':
            if len(msg['slaves']) == 0:
                print "I'm the first"
            for remote in msg['slaves']:
                (self.address, delay, rate) = self.speed(remote)
                # do some thing记录延迟map
            self.qw.put_nowait({'udp_address': self.address})

    def msg_from_parent(self,):
        if not self.qr.empty():
            msg = self.qr.get_nowait()
            return msg
        else:
            print "empty queue"
            return None

    def deal_udp_msg(self,):
        data, address = self.msg_from_remote_udp()
        if not data:
            print "something is wrong"
        # print "receive ", data, "from", address
        msg = json.loads(data)
        func_dict = {
            'speed': self.deal_speed,
            'forward': self.deal_forward,
            'speedCallback': self.deal_speed_callback,
        }
        func = func_dict.get(msg['flag'])
        func(address, msg)

    def msg_from_remote_udp(self):
        data, address = self.server.recvfrom(4096)
        return data, address

    def mainloop(self):
        self.init_server()
        print "UDP server start"
        # print "parent pid: ", str(os.getppid())
        print "pid: " + str(os.getpid())
        while True:
            self.deal_parent_msg()
            self.deal_udp_msg()

    def speed(self, address):
        print 'start speed test to ', address
        now = time.time()
        self.speedMap[address] = now
        self.speedRes[address] = -1
        address = (item for item in address.split(':'))
        self.server.sendto("speed", address)

    def deal_speed_callback(self, address, data):
        now = time.time()
        address = ';'.join(address)
        delay = (now - self.speedMap[address]) * 1000
        print "modifying ", address
        self.speedRes[address] = delay

    def deal_speed(self, address, data):
        # tmp = address.split(":")
        # address = (tmp[0], tmp[1])
        self.server.sendto("speedCallback", address)

    def deal_forward(self, address, data):
        pass

    def __del__(self):
        self.server.close()


def start_udp_server(qr, qw):
    udp_server = UDPServer(qr, qw)
    udp_server.mainloop()

