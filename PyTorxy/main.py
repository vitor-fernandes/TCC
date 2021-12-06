import HTTProxy
import SOCKSProxy
import sys

def get_help():
    print('HELP')

def launch_server(type, host, port, IPv6):
    
    proxy_instance = ''

    if(type == 'http'):
        proxy_instance = HTTProxy
    elif(type == 'socks'):
        proxy_instance = SOCKSProxy
    else:
        print('Invalid Proxy Type')
        exit(1)

    proxy_instance.Start_Proxy(host, port, IPv6)


def main():
    launch_server('http', '127.0.0.1', 8051, False)

main()

