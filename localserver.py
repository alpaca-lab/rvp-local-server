import socket
import json

host = '112.124.104.95'
port = 9999
remote = (host, port)
class LocalServer():
    def __init__(self):
        self.slave = None
        self.server = None

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
