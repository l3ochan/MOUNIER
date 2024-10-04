from dotenv import load_dotenv
import os, socket, json 


load_dotenv('.env')
server_ip = os.getenv('SERVER_IP')
server_port = int(os.getenv('SERVER_PORT'))

def send_request(request):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))
    client_socket.sendall(json.dumps(request).encode('utf-8'))
    response_data = client_socket.recv(4096).decode('utf-8')
    response = json.loads(response_data)
    print(response)
    client_socket.close()

# Exemple : créer une promotion
request = {
    "action": "create_promotion",
    "data": {
        "nom": "Promo2024",
    }
}
send_request(request)
