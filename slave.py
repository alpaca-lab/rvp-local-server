from localserver import start_slave_server
import multiprocessing

if __name__ == '__main__':
    multiprocessing.freeze_support()
    start_slave_server()
