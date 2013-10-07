import socket
import struct
import hashlib
import base64
import threading
import sys

sys.setrecursionlimit(1000000)
connectionlist={}
server_address=("localhost",88)

def sendAll(message):
    global connectionlist
    for connection in connectionlist.values():
        webSocket.senddata(connection,message)

def deleteconnection(item):
    global connectionlist
    if connectionlist.has_key('connection'+str(item)):
        del connectionlist['connection'+str(item)]
    

class webSocket(threading.Thread):
    def __init__(self,conn,index,name,address,path="/"):
        threading.Thread.__init__(self)
        self.conn=conn
        self.index=index
        self.name=name
        self.address=address
        self.path=path

    def handshake(self,conn):
        headers={}
        key = None 
        data = conn.recv(8192)
        if not len(data):
            return False
        for line in data.split('\r\n\r\n')[0].split('\r\n')[1:]:
            k, v = line.split(': ')
            if k=="Sec-WebSocket-Key":
                key = base64.b64encode(hashlib.sha1(v + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').digest())
        if not key:
            conn.close()
            return False
        response = 'HTTP/1.1 101 Switching Protocols\r\n'\
                    'Upgrade: websocket\r\n'\
                    'Connection: Upgrade\r\n'\
                    'Sec-WebSocket-Accept:' + key + '\r\n\r\n'
        conn.send(response)
        return True

    def receive(self,conn, size=8192):
        data = conn.recv(size)
        if not len(data):
            return False
        length = ord(data[1]) & 127
        if length == 126:
            mask = data[4:8]
            raw = data[8:]
        elif length == 127:
            mask = data[10:14]
            raw = data[14:]
        else:
            mask = data[2:6]
            raw = data[6:]
        ret = ''
        for cnt, d in enumerate(raw):
            ret += chr(ord(d) ^ ord(mask[cnt%4]))
        return ret
                          
    @staticmethod                      
    def senddata(conn, data):
        head = '\x81'
        if len(data) < 126:
            head += struct.pack('B', len(data))
        elif len(data) <= 0xFFFF:
            head += struct.pack('!BH', 126, len(data))
        else:
            head += struct.pack('!BQ', 127, len(data))
        conn.send(head+data)


    
    def run(self):
        print'Socket%s Start!' %self.index
        self.handsuccess=False
        connect=self.conn
        while True:
            if self.handsuccess==False:
                print'Socket%s start Handshake with %s!'%(self.index,self.address)
                if  self.handshake(connect):
                    print 'Socket%s Handshaken with %s success!' % (self.index,self.address)
                    sendAll('Welcome, '+self.name+' !')
                    self.handsuccess=True

                    
            else:
                message=self.receive(connect)
                if not message:
                    deleteconnection(self.index)
                    self.conn.close()
                    break
                if message=='quit':
                    print 'Socket%s Logout!'%(self.index)
                    sendAll(self.name+'Logout')
                    deleteconnection(self.index)
                    self.conn.close()
                    break
                else:
                    print 'Socket%s Got msg:%s from %s!' % (self.index,message,self.address)
                    sendAll(self.name+':'+str(message))

                

class webSocketServer(object):
    def __init__(self):
        self.socket=None
    def begin(self):
        print 'WebSocketServer Start!'
        self.socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket.bind(server_address)
        self.socket.listen(100)

        i=0
        while True:
            connection,address=self.socket.accept()
            username=address[0]

            newSocket=webSocket(connection,i,username,address)
            newSocket.start()
            connectionlist['connection'+str(i)]=connection
            i=i+1
if __name__=="__main__":
    server=webSocketServer()
    server.begin()
        
