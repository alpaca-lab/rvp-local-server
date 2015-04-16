import socket
import json
from udpserver import UDPServer
from multiprocessing import Process
host = '112.124.104.95'
port = 9999
remote = (host, port)


class LocalServer():
    def __init__(self):
        self.slave = None
        self.server = None
        self.all_slaves = None
        self.udp_server = UDPServer()

    def init_slave(self):
        slave = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        slave.setblocking(False)
        slave.connect(remote)
        self.slave = slave

    def get_all_slaves(self):
        msg = json.dumps({
            'req': 'get_slaves',
        })
        self.slave.send(msg)
        data = self.slave.recv(1024)
        self.all_slaves = json.loads(data)['slaves']

    def speed_test(self):
        flag = self.udp_server.speedtest(self.all_slaves)
        if not flag:
            exit(1)

    def register_this_server(self):
        msg = json.dumps({
            'req': 'register',
            'address': self.udp_server.address
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
        self.udp_server.start()
        while True:
            self.mainloop()