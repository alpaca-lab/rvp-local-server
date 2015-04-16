import socket
import json
from udpserver import UDPServer
from multiprocessing import Process, Queue
import time
host = '112.124.104.95'
port = 9999
remote = (host, port)


class LocalServer():
    def __init__(self):
        self.slave = None
        self.server = None
        self.all_slaves = None
        self.udp_server = None
        self.udp_process = None
        self.udp_address = None
        self.qr = Queue()
        self.qw = Queue()

    def init_slave(self):
        slave = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        slave.setblocking(False)
        slave.connect(remote)
        self.udp_server = UDPServer(self.qw, self.qr)
        self.udp_process = self.udp_server.start_server()
        self.slave = slave

    def get_all_slaves(self):
        msg = json.dumps({
            'req': 'get_slaves',
        })
        self.slave.send(msg)
        data = self.slave.recv(1024)
        self.all_slaves = json.loads(data)['slaves']

    def msg_to_udp_server(self, msg):
        try:
            self.qw.put_nowait(msg)
        except Exception, e:
            print e
            exit(1)

    def msg_from_udp_server(self):
        if not self.qr.empty():
            msg = self.qr.get_nowait()
            return msg
        else:
            print "empty queue"
            return None

    def speed_test(self):
        self.msg_to_udp_server({
            'op': 'speed_test',
            'slaves': self.all_slaves,
        })
        msg = self.msg_from_udp_server()
        while msg is None:
            msg = self.msg_from_udp_server()
            time.sleep(5)
        self.udp_address = msg['udp_address']

    def register_this_server(self):
        msg = json.dumps({
            'req': 'register',
            'address': self.udp_address
        })
        self.slave.send(msg)
        data = self.slave.recv(1024)
        msg = json.loads(data)
        if msg['ans'] != 'success':
            exit(1)

    def mainloop(self):
        data = self.slave.recv(1024)

    def start_slave_server(self):
        self.init_slave()
        self.get_all_slaves()
        self.speed_test()
        self.register_this_server()
        while True:
            self.mainloop()