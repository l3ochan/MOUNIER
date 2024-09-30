import socket
import threading

def handle_client(conn, addr):
    print(f"Nouveau client connecté : {addr}")
    try:
        while True:
            request = conn.recv(1024)
            if not request:  # Vérifie si la connexion est fermée par le client
                break
            print(request.decode("utf-8"))  # Affiche les données du client
    finally:
        conn.close()  # S'assurer que la connexion est fermée ici
        print(f"Connexion fermée : {addr}")

def start_server(host='', port=62154):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()
    print(f"Serveur en écoute sur {host}:{port}")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    start_server()