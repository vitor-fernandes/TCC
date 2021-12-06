import logging
import select
import socket
import struct
import threading
import re
import socks

logging.basicConfig(level=logging.DEBUG)
SOCKS_VERSION = 5

class ProxyHandler(threading.Thread):

    def __init__(self, connection):
        threading.Thread.__init__(self)
        self.client_address = connection[1]
        self.client_socket = connection[0]
        self.connection = connection
    
    def run(self):
        logging.info('Accepting connection from %s:%s' % self.client_address)

        # greeting header
        # read and unpack 2 bytes from a client
        header = self.client_socket.recv(2)
        version, nmethods = struct.unpack("!BB", header)
        
        # send welcome message
        self.client_socket.sendall(struct.pack("!BB", SOCKS_VERSION, 0))

        # request
        tmp = self.client_socket.recv(8192)

        version, cmd, _, address_type = struct.unpack("!BBBB", self.client_socket.recv(4))

        print(version, cmd, _, address_type)

        if address_type == 1:  # IPv4
            address = socket.inet_ntoa(self.client_socket.recv(4))

        elif address_type == 3:  # Domain name
            connection_recv = self.client_socket.recv(8192)
            size_address = len(connection_recv)

            print(connection_recv)
            print(self.connection)

            #raw_address = ''.join([chr(char) for char in struct.unpack("!{}".format('B' * size_address), connection_recv)])
            raw_address = ''.join([chr(char) for char in connection_recv])
    
            # Remove the last char (») from address
            address = raw_address[1:-2]

        tmp = self.client_socket.recv(8192)
        print(tmp)

        port = struct.unpack('!H', self.client_socket.recv(2))

        # reply
        try:
            if cmd == 1:  # CONNECT
                #remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                (socket_family, _, _, _, address_target) = socket.getaddrinfo(address, int(port))[0]

                remote_socket = socks.socksocket(socket_family)
                remote_socket.connect(address_target)
                bind_address = remote_socket.getsockname()
                logging.info('Connected to %s %s' % (address, port))
            #else:
                #self.client_socket.close()
                #self.server.close_request(self.request)

            addr = struct.unpack("!I", socket.inet_aton(bind_address[0]))[0]
            port = bind_address[1]
            reply = struct.pack("!BBBBIH", SOCKS_VERSION, 0, 0, address_type,
                                addr, port)
            print(reply)

        except Exception as err:
            print('err')
            logging.error(err)
            # return connection refused error
            reply = self.generate_failed_reply(address_type, 5)

        self.client_socket.sendall(reply)

        # establish data exchange
        if reply[1] == 0 and cmd == 1:
            self.exchange_loop(self.client_socket, remote_socket)

        #self.server.close_request(self.request)
        self.client_socket.close()

    def get_available_methods(self, n):
        methods = []
        for i in range(n):
            methods.append(ord(self.client_socket.recv(1)))
        return methods

    def generate_failed_reply(self, address_type, error_number):
        return struct.pack("!BBBBIH", SOCKS_VERSION, error_number, 0, address_type, 0, 0)

    def exchange_loop(self, client, remote):

        while True:

            # wait until client or remote is available for read
            r, w, e = select.select([client, remote], [], [])

            if client in r:
                data = client.recv(4096)
                if remote.send(data) <= 0:
                    break

            if remote in r:
                data = remote.recv(4096)
                if client.send(data) <= 0:
                    break
    

class Start_Proxy():

    def __init__(self, host, port, IPv6):
        self.host = host
        self.port = port
        self.IPv6 = IPv6
    
        self.start_server()

    def start_server(proxy_object):
        # Tor Proxy
        #socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, '127.0.0.1', 9050)

        server_socket = socks.socksocket(socket.AF_INET)
        
        # Prevent waiting previous socket with TIME_AWAIT
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        server_socket.bind(( proxy_object.host, proxy_object.port ))

        print('Serving at {}:{}'.format(proxy_object.host, proxy_object.port))

        server_socket.listen(0)

        while(KeyboardInterrupt):
            new_thread = ProxyHandler(server_socket.accept())
            new_thread.start()

        server_socket.close()