# Ce petit programme recoit un array de bits en UDP

import socket
# initialisation du serveur
serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

port = 62154
serveur.bind(('', port)) # Ecoute sur le port 62154
serveur.listen()
print(f"TCP Server listening on port {port}")

while True :
    client, infosclient = serveur.accept()
    request = client.recv(1024)
    print(request.decode("utf-8")) #affiche les données du client
    local_ip, local_port = client.getsockname()
    print(f"Adresse IP du client : {local_ip}, Port : {local_port}")
    client.close()
serveur.close()
