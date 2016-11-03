import signal
import sys
import socket  
import time
import datetime
from TCPconfig import *

global isSIGINT
def SIGINT_handler(signum, frame): # do some clean up when being Interrupted
    global isSIGINT
    isSIGINT = True
    print("Process terminated!\n")

signal.signal(signal.SIGINT, SIGINT_handler)
isSIGINT = False
# The adress of the server, as well as the port number
address = (host_address, port_phone)
ra = []
if __name__ == '__main__':
    socket.setdefaulttimeout(timeout)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # s = socket.socket()  
    s.bind(address) 
    while(not isSIGINT):
        while(not isSIGINT):
            print('Waiting for connections...')
            try:
                s.listen(5)  
                ss, addr = s.accept() 
            except:
                print("Listen timeout\n")
            else:
                print(['got connected from', addr])
                time.sleep(0.5)
                break
        
        while(not isSIGINT):
            try:
                ra = ss.recv(512)
                print(ra)
            except:
                print('Read timeout\n')
                ss.close()
                isValidConn = False
                continue
            else:
                ss.send(ra)
    try:
        ss.close()
    except:
        print("socket serverice not created\n")

    s.close()
    sys.exit()
    print("Bye\b")
        