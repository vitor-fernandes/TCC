import threading
import socket
import socks
import select

import IPChanger

BUFF = 8192

class ProxyHandler(threading.Thread):
    def __init__(self, connection):
        threading.Thread.__init__(self)
        self.client_socket = connection[0]
        self.client_data = bytearray()

        self.timeout = 60
        self.method = ''
        self.url = ''
        self.http_version = ''
        #self.q = bytearray()

        self.target_socket = ''
    
    def run(self):
        self.get_headers()

        print(self.client_data)

        if('CONNECT' in self.method):
            self.do_CONNECT()
        
        elif(self.method in ('OPTIONS', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'TRACE')):
            self.do_ANY_METHOD()
        
        self.client_socket.close()
        self.target_socket.close()

    def get_headers(self):
        try:
            final = -1
            while(final == -1):
                self.client_data.extend(self.client_socket.recv(8192))
                final = self.client_data.find('\n'.encode())
            
            self.method, self.url, self.http_version = self.client_data.split('\n'.encode())[0].split(' '.encode())
            
            self.method = self.method.decode()
            self.url = self.url.decode()
            self.http_version = self.http_version.decode()
            
            self.client_data = self.client_data[final+1:]
        except:
            print('Except')    
    # HTTP METHODS SECTION START
    def do_CONNECT(self):
        self.connect_to_host(self.url)
        # Send a OK Response to the Client
        self.client_socket.send("{} 200 Connection established\r\nProxy-agent: PyTorxy\r\n\n".format(self.http_version).encode())
        
        # Flush the Client Data
        self.client_data = bytearray()

        # Start to change data
        self.transfer_data()
    
    def do_ANY_METHOD(self):
        # Remove the Protocol
        target = self.url[7:]
        index = target.find('/')
        host = target[:index]        
        path = target[index:]

        if('http://' in self.url):
            host = self.url.split('/')[2]
            path = self.url
        
        self.connect_to_host(host)
        
        tmp_data = bytearray()
        tmp_data.extend(self.method.encode())
        tmp_data.extend(" {}".format(path).encode())
        tmp_data.extend(" {}\n".format(self.http_version).encode())
        tmp_data.extend(self.client_data)

        # Send the Data received from Client to Target
        self.target_socket.send(tmp_data)
        
        # Flush the Client Data
        self.client_data = bytearray()

        # Start Data Transfer
        self.transfer_data()
    # HTTP METHODS SECTION END

    def connect_to_host(self, host):
        target = host
        port = 80

        if(':' in host):
            target, port = host.split(':')
        
        # Get information about the target: IPv4 || IPv6 and Address
        (socket_family, _, _, _, address) = socket.getaddrinfo(target, int(port))[0]

        # Create a new Socket with the Target and Connect
        self.target_socket = socks.socksocket(socket_family)
        self.target_socket.connect(address)
        change_ip()
    
    def transfer_data(self):
        time_out_max = self.timeout
        socs = [self.client_socket, self.target_socket]
        count = 0
        while 1:
            count += 1
            (recv, _, error) = select.select(socs, [], socs, 3)
            if error:
                break
            if recv:
                for in_ in recv:
                    data = in_.recv(8192)
                    if in_ == self.client_socket:
                        out = self.target_socket
                    else:
                        out = self.client_socket
                    if data:
                        out.send(data)
                        count = 0
            if count == time_out_max:
                break  


def change_ip():
    IPChanger.swap_ip('Testing666')

class Start_Proxy():

    def __init__(self, host, port, IPv6):
        self.host = host
        self.port = port
        self.IPv6 = IPv6

        self.start_server()

    def start_server(proxy_object):
        
        socket_family = socket.AF_INET
        if(proxy_object.IPv6):
            socket_family = socket.AF_INET6
        
        # Tor Proxy
        socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, '127.0.0.1', 9050)

        server_socket = socks.socksocket(socket_family)
        
        # Prevent waiting previous socket with TIME_AWAIT
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        server_socket.bind(( proxy_object.host, proxy_object.port ))

        print('Serving at {}:{}'.format(proxy_object.host, proxy_object.port))

        server_socket.listen(0)

        while(KeyboardInterrupt):
            new_thread = ProxyHandler(server_socket.accept())
            new_thread.start()

        server_socket.close()
