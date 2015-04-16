from localserver import LocalServer
import multiprocessing

if __name__ == '__main__':
    multiprocessing.freeze_support()
    server = LocalServer()
    server.start_slave_server()
