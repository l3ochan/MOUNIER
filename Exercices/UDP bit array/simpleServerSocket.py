# Ce petit programme recoit un array de bits en UDP

import socket
# initialisation du serveur
serveur = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

port = 62154
serveur.bind(('', port)) # Ecoute sur le port 62154
print(f"UDP Server listening on port {port}")

while True:
    message, addr = serveur.recvfrom(1024)
    local_ip, local_port = addr
    print(f"Message reçu : {message.decode()}")
    print(f"Adresse IP du client : {local_ip}:{local_port}")
serveur.close()
