# Ce petit programme envoie un array de bits en UDP

import socket
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
port = 62154
server_ip = "nekoserv.diplodocus-anaconda.ts.net"
client.connect((server_ip, port))
print(f"connecting to {server_ip}:{port}")
client.sendall(b"hello serveur\n")
client.close()


