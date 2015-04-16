import socket
from datetime import datetime
import threading


class UDPServer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
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
        while True:
            data, address = self.server.recvfrom(4096)
            if not data:
                print "something is wrong"
                break
            print "receive ", data, "from", address

            flag = data.split('#')[0]
            if flag == 'speed':
                self.deal_speed(address)
            elif flag == 'forward':
                self.deal_forward(data)
            elif flag == 'speedCallback':
                self.deal_speed_callback(address)

    def speed(self, address):
        tmp = str(datetime.now()).split(":")
        now = int(float(tmp[len(tmp) - 1]) * 1000000)
        self.speedMap[address] = now
        self.speedRes[address] = -1
        tmp = address.split(":")
        address = (tmp[0], int(tmp[1]))
        self.server.sendto("speed", address)

    def deal_speed_callback(self, address):
        tmp = str(datetime.now()).split(":")
        now = int(float(tmp[len(tmp) - 1]) * 1000000)
        time = (now - self.speedMap[str(address[0]+":"+str(address[1]))]) / 1000
        print "modifying ", str(address[0])+":"+str(address[1])
        self.speedRes[str(address[0])+":"+str(address[1])] = time

    def deal_speed(self, address):
        # tmp = address.split(":")
        # address = (tmp[0], tmp[1])
        self.server.sendto("speedCallback", address)

    def deal_forward(self, data):
        pass

    def __del__(self):
        self.server.close()


if __name__ == "__main__":
    server = UDPServer()
    server.init_server()
    server.start()
    server.join()
    print "server shutdown"