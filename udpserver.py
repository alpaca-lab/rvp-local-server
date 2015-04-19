# coding: utf-8
import json
import time
import socket
import logging
import os


class UDPServer():
    def __init__(self, qr, qw):
        self.server = None
        # 每个UDPServer测速的次数
        self.tryCount = 1000
        # 记录测速结果的list，目标地址，延迟，丢包率
        self.speedMap = {
            'localhost': {
                'delay': 0,
                'missRate': 0
            }
        }
        # 记录对战的map, key是userName, val是目标地址
        self.battleMap = {}
        self.address = None
        # 进程间交互使用的队列
        self.q_from_parent = qr
        self.q_to_parent = qw
        # 处理各种信息使用的函数的dict，代替case语句
        self.udp_func_dict = {
            'speed': self.deal_speed,
            'forward': self.deal_forward,
            'speedCallback': self.deal_speed_callback,
        }
        self.parent_func_dict = {
            'speed_test': self.speed_test_start
        }

    # 把address的tuple转成字符串和逆转换
    @staticmethod
    def str2address(address_str):
        str_list = address_str.split(':')
        return str_list[0], int(str_list[1])

    @staticmethod
    def address2str(address):
        return ":".join([str(item) for item in address])

    # 初始化, 启动udp server并绑定端口
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

    # 处理从父进程的tcpServer过来的信息, 以及双方信息交互
    def deal_parent_msg(self, ):
        msg = self.msg_from_parent()
        if msg is None:
            return
        func = self.parent_func_dict.get(msg['op'])
        func(msg)

    def msg_from_parent(self, ):
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

    # 处理从远程udpServer过来的信息，以及双方信息交互
    def deal_udp_msg(self, ):
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

    # 开始主循环
    def start(self):
        while True:
            self.deal_parent_msg()
            self.deal_udp_msg()
            print "one udp loop"

    # 处理tcpServer传过来的各种不同信息的函数
    def speed_test_start(self, msg):
        if len(msg['slaves']) == 0:
            print "I'm the first"
            self.speed_test_end()
        for address_str in msg['slaves']:
            print 'start speed test to ', address_str
            self.speed_test_one_remote(address_str)

    def speed_test_end(self):
        self.msg_to_parent({'udp_address': self.address})

    def speed_test_one_remote(self, address_str):
        address = (self.str2address(address_str))
        self.msg_to_remote_udp({
                               "op": "speed",
                               'sent': time.time()
                               }, address)

    # 处理udpServer传过来的各种不同信息的函数
    def deal_speed_callback(self, address, msg):
        now = time.time()
        address_str = self.address2str(address)
        delay = (now - msg['sent']) * 1000
        print "modifying ", address, ", delay: ", delay
        self.speedMap[address_str]['delay'] = delay
        self.address = msg['address']
        self.speed_test_end()

    def deal_speed(self, address, msg):
        self.msg_to_remote_udp({
                               "op": "speedCallback",
                               'sent': msg['sent'],
                               "address": self.address2str(address)
                               }, address)

    def deal_forward(self, address, msg):
        self.msg_to_remote_udp(msg, self.battleMap[msg['user']])
        pass

    def __del__(self):
        self.server.close()


def start_udp_server(qr, qw):
    udp_server = UDPServer(qr, qw)
    udp_server.init_server()
    print "UDP server start"
    print "pid: " + str(os.getpid())
    udp_server.start()

