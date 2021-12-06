import socket

def swap_ip(password):
    # Comunicate with Tor Control Port
    tor_control_socket = socket.create_connection(( "127.0.0.1", 9051 ))

    # Send a Signal to Tor Control to Change the Circuit and close the connection
    tor_control_socket.send('AUTHENTICATE "{}"\r\nSIGNAL NEWNYM\r\nQUIT\r\n'.format(password).encode())
    tor_control_socket.close()
        