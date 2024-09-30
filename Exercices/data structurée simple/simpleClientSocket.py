# Ce petit programme envoie un array de bits en UDP

import socket
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
port = 62154
server_ip = "nekoserv.diplodocus-anaconda.ts.net"
client.connect((server_ip, port))
client_ip, client_port = client.getsockname()
encoded_ip=bytearray(list(map(int, client_ip.split('.'))))
print(f"connecting to {server_ip}:{port}")

client.sendall(f"my ip adresse is {encoded_ip}".encode())
client.close()


