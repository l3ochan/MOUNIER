from dotenv import load_dotenv
import os, socket, json 


load_dotenv('.env')
server_ip = os.getenv('SERVER_IP')
server_port = int(os.getenv('SERVER_PORT'))

def send_request(request):
    try: 
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_ip, server_port))
        client_socket.sendall(json.dumps(request).encode('utf-8'))
        response_data = client_socket.recv(4096).decode('utf-8')
        response = json.loads(response_data)
        print(response)
        client_socket.close()
    except Exception as e:
        print(f"Une erreur est survenue lors de l'envoi de la requête : {e}")
        return {'status': 'error', 'message': str(e)}

def create_promotion(nom):
    request = {
        "action": "create_promotion",
        "data": {
            "nom": nom
        }
    }
    response = send_request(request)
    return response

def add_student(nom, prenom, promo_nom):
    request = {
        "action": "add_student",
        "data": {
            "nom": nom,
            "prenom": prenom,
            "promo_nom": promo_nom
        }
    }
    response = send_request(request)
    return response



def add_note(etudiant_nom, etudiant_prenom, valeur, coef):
    request = {
        "action": "add_note",
        "data": {
            "etudiant_nom": etudiant_nom,
            "etudiant_prenom": etudiant_prenom,
            "valeur": valeur,
            "coef": coef
        }
    }
    response = send_request(request)
    return response



def calculate_student_average(etudiant_nom, etudiant_prenom):
    request = {
        "action": "calculate_student_average",
        "data": {
            "etudiant_nom": etudiant_nom,
            "etudiant_prenom": etudiant_prenom
        }
    }
    response = send_request(request)
    return response



def calculate_promotion_average(promo_nom):
    request = {
        "action": "calculate_promotion_average",
        "data": {
            "promo_nom": promo_nom
        }
    }
    response = send_request(request)
    return response



def get_student_details(etudiant_nom, etudiant_prenom):
    request = {
        "action": "get_student_details",
        "data": {
            "etudiant_nom": etudiant_nom,
            "etudiant_prenom": etudiant_prenom
        }
    }
    response = send_request(request)
    return response




# =====friendly commands===== 
# Définir les commandes et indiquer si elles acceptent des paramètres (True) ou non (False)
commands = {
    "create student": (add_student, True),
    "create prom": (create_promotion, True),
    "grade add": (add_note, True),
    "calculate student average": (calculate_student_average, True),  # Cette fonction accepte des paramètres
    "calculate prom average": (calculate_promotion_average, True),
    "help" : (help, True),
    "details student" : (get_student_details, True), #cette fonction n'en accepte pas
    }

def process_command(input_command):
    parts = input_command.split(' ')
    found_command = None
    params = []

    # Identifier la commande la plus longue qui correspond
    for cmd in sorted(commands.keys(), key=len, reverse=True):
        if input_command.startswith(cmd):
            found_command = cmd
            break

    if found_command:
        func, accepts_params = commands[found_command]
        # Extraire les paramètres si présents
        if len(input_command) > len(found_command):
            # Assurez-vous qu'il y a un espace après la commande avant de prendre des paramètres
            if input_command[len(found_command)] == ' ':
                params = input_command[len(found_command)+1:].split(' ')
        
        # Exécuter la commande avec ou sans paramètres selon le cas
        if accepts_params:
            if len(params) == 0:
                print(f"Error: Missing required parameter for command '{found_command}'.")
            else:
                func(*params)
        else:
            if len(params) > 0:
                print(f"Error: Command '{found_command}' does not accept parameters.")
            else:
                func()
    else:
        print("Unknown command, for a list of commands, type 'help'.")


# Boucle principale pour lire les commandes de l'utilisateur
while True:
    user_input = input(">")
    if user_input == "exit":
        break
    process_command(user_input)