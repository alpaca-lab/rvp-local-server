import socket
import threading
from datetime import datetime
import time
from udpserver import UDPServer
hosts = ['127.0.0.1:30000']

server = UDPServer()
server.init_server()
server.start()


server.speed(hosts[0])
time.sleep(2)
print server.speedRes
server.join()
