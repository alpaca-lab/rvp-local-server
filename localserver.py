import socket
import json
from udpserver import start_udp_server
from multiprocessing import Process, Queue
import time
import logging
# host = '112.124.104.95'
port = 9998
host = 'localhost'
remote = (host, port)


class LocalServer():
    udp_func_dict = {

    }
    remote_func_dict = {

    }

    def __init__(self):
        self.slave = None
        self.server = None
        self.all_slaves = None
        self.udp_address = None
        self.q_from_udp_server = Queue()
        self.q_to_udp_server = Queue()
        self.udp_process = None

    def init_slave(self):
        print 'initializing server'
        slave = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        slave.connect(remote)
        slave.setblocking(False)
        self.udp_process = Process(target=start_udp_server, args=(self.q_to_udp_server, self.q_from_udp_server))
        self.udp_process.start()
        self.slave = slave

    def get_all_slaves(self):
        print 'getting all slaves'
        self.msg_to_remote_server({
            'op': 'get_slaves',
        })
        msg = None
        while msg is None:
            msg = self.msg_from_remote()
        self.all_slaves = msg['slaves']
        print "all slaves: ", self.all_slaves

    def speed_test(self):
        print 'start speed_test'
        self.msg_to_udp_server({
            'op': 'speed_test',
            'slaves': self.all_slaves,
        })
        msg = self.msg_from_udp_server()
        while msg is None:
            msg = self.msg_from_udp_server()
            time.sleep(1)
        self.udp_address = msg['udp_address']
        print 'udp_address', self.udp_address

    def register_this_server(self):
        print 'register this server'
        self.msg_to_remote_server({
            'op': 'register',
            'address': self.udp_address
        })
        msg = None
        while msg is None:
            msg = self.msg_from_remote()
        if msg['ans'] != 'success':
            exit(1)

    def mainloop(self):
        while True:
            self.deal_msg_from_udp_server()
            self.deal_msg_from_remote()

    def deal_msg_from_udp_server(self):
        msg = self.msg_from_udp_server()
        if msg is None:
            return
        func = self.udp_func_dict.get(msg['op'])
        if func is None:
            print "error msg from udp server"
            return
        func(msg)

    def deal_msg_from_remote(self):
        msg = self.msg_from_remote()
        if msg is None:
            return
        func = self.remote_func_dict.get(msg['op'])
        if func is None:
            print "error msg from remote server"
            return
        func(msg)

    def msg_from_udp_server(self):
        if not self.q_from_udp_server.empty():
            msg = self.q_from_udp_server.get_nowait()
            print "message from udp server: ", msg
            return msg
        else:
            # print "empty queue"
            return None

    def msg_from_remote(self):
        try:
            data = self.slave.recv(1024)
        except Exception, e:
            return None
        msg = json.loads(data)
        print "message from remote: ", msg
        return msg

    def msg_to_udp_server(self, msg):
        print "send msg to udp server", msg
        try:
            self.q_to_udp_server.put_nowait(msg)
        except Exception, e:
            print e
            print "send message to udp server error"

    def msg_to_remote_server(self, msg):
        print "send msg to remote server", msg
        try:
            data = json.dumps(msg)
            self.slave.send(data)
        except Exception, e:
            print e.message
            print "send message to remote server error"

    def __del__(self):
        self.server.close()


def start_slave_server():
    server = LocalServer()
    server.init_slave()
    server.get_all_slaves()
    server.speed_test()
    server.register_this_server()
    server.mainloop()

