# coding: utf-8
import json
import time
import socket
import logging
import os


class UDPServer():

    def __init__(self, qr, qw):
        self.server = None
        self.tryCount = 1000
        self.speedMap = {}
        self.speedRes = {}
        self.address = None
        self.q_from_parent = qr
        self.q_to_parent = qw
        self.udp_func_dict = {
            'speed': self.deal_speed,
            'forward': self.deal_forward,
            'speedCallback': self.deal_speed_callback,
        }
        self.parent_func_dict = {
            'speed_test': self.speed_test_start
        }

    @staticmethod
    def str2address(address_str):
        str_list = address_str.split(':')
        return str_list[0], int(str_list[1])

    @staticmethod
    def address2str(address):
        return ":".join([str(item) for item in address])

    def init_server(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        address = ('192.168.1.204', 30000)
        while True:
            try:
                self.server.bind(address)
                print "UDP server bind to ", address
                self.address = self.address2str(address)
                break
            except Exception, e:
                print e
                address = (address[0], address[1] + 1)

    def deal_parent_msg(self,):
        msg = self.msg_from_parent()
        if msg is None:
            return
        func = self.parent_func_dict.get(msg['op'])
        func(msg)

    def msg_from_parent(self,):
        if not self.q_from_parent.empty():
            msg = self.q_from_parent.get_nowait()
            print 'receive', msg, ' from parent'
            return msg
        else:
            # print "empty queue"
            return None

    def msg_to_parent(self, msg):
        try:
            self.q_to_parent.put_nowait()
        except Exception, e:
            print e.message

    def deal_udp_msg(self,):
        msg, address = self.msg_from_remote_udp()
        func = self.udp_func_dict.get(msg['op'])
        func(address, msg)

    def msg_from_remote_udp(self):
        data, address = self.server.recvfrom(4096)
        print "receive ", data, "from", address
        if not data:
            print "empty message from remote udp server"
        return json.loads(data), address

    def msg_to_remote_udp(self, msg, address):
        try:
            self.server.sendto(json.dumps(msg), address)
        except Exception, e:
            print e

    def start(self):
        while True:
            self.deal_parent_msg()
            self.deal_udp_msg()
            print "one udp loop"

    def speed_test_start(self, msg):
        if len(msg['slaves']) == 0:
            print "I'm the first"
            self.speed_test_end()
        for address_str in msg['slaves']:
            print 'start speed test to ', address_str
            now = time.time()
            self.speedMap[address_str] = now
            self.speedRes[address_str] = -1
            address = (self.str2address(address_str))
            self.msg_to_remote_udp({
                "op": "speed"
            }, address)

    def speed_test_end(self):
        self.msg_to_parent({'udp_address': self.address})

    def deal_speed_callback(self, address, msg):
        now = time.time()
        address_str = self.address2str(address)
        delay = (now - self.speedMap[address_str]) * 1000
        print "modifying ", address, ", delay: ", delay
        self.speedRes[address_str] = delay
        self.address = msg['address']
        self.speed_test_end()

    def deal_speed(self, address, msg):
        self.msg_to_remote_udp({
            "op": "speedCallback",
            "address": self.address2str(address)
        }, address)

    def deal_forward(self, address, data):
        pass

    def __del__(self):
        self.server.close()


def start_udp_server(qr, qw):
    udp_server = UDPServer(qr, qw)
    udp_server.init_server()
    print "UDP server start"
    print "pid: " + str(os.getpid())
    udp_server.start()

