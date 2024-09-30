# Ce petit programme envoie un array de bits en UDP

import socket
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
port = 62154
server_ip = "nekoserv.diplodocus-anaconda.ts.net"
print(f"sending to {server_ip}:{port} with UDP proto")
client.sendto(b"hello serveur\n", (server_ip, port))
client.close()


