from dotenv import load_dotenv
import os, socket, threading, mysql.connector, json 
from mysql.connector import Error


load_dotenv()
listening_ip = os.getenv('LISTENING_IP')
listening_port = int(os.getenv('LISTENING_PORT'))
db_host = os.getenv('DATABASE_HOST')
db_port = int(os.getenv('DATABASE_PORT'))
db_user = os.getenv('DATABASE_USER')
db_password = os.getenv('DATABASE_PASSWORD')
db_name = os.getenv('DATABASE_NAME')


def get_db_connection():
    return mysql.connector.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name
    )



# Créer une socket TCP/IP
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((listening_ip, listening_port))
server_socket.listen()

print(f"Le serveur écoute sur {listening_ip}:{listening_port}")

# Fonction pour gérer les connexions des clients
def handle_client(client_socket, address):
    print(f"Connexion établie avec {address}")
    try:
        # Gestion des requêtes du client
        handle_requests(client_socket)
    finally:
        client_socket.close()

def handle_requests(client_socket):
    try:
        # Recevoir les données du client
        data = client_socket.recv(4096).decode('utf-8')
        if not data:
            return
        request = json.loads(data)
        action = request.get('action')
        response = {}

        # Établir une connexion à la base de données pour ce thread
        connection = get_db_connection()

        if action == 'create_promotion':
            promo_data = request.get('data')
            cursor = connection.cursor()
            sql = "INSERT INTO Promotions (nom) VALUES (%s)"
            cursor.execute(sql, (promo_data['nom'],))  # La virgule est importante ici
            connection.commit()
            cursor.close()
            response['status'] = 'success'
            response['message'] = 'Promotion créée avec succès.'


        elif action == 'add_student':
            student_data = request.get('data')
            nom = student_data['nom']
            prenom = student_data['prenom']
            promo_nom = student_data['promo_nom']
            cursor = connection.cursor()

            # Trouver l'ID de la promotion à partir du nom
            sql = "SELECT id FROM Promotions WHERE nom = %s"
            cursor.execute(sql, (promo_nom,))
            result = cursor.fetchone()
            if result:
                promo_id = result[0]
                # Insérer l'étudiant
                sql = "INSERT INTO Etudiants (nom, prenom, promo_id) VALUES (%s, %s, %s)"
                cursor.execute(sql, (nom, prenom, promo_id))
                connection.commit()
                etudiant_id = cursor.lastrowid
                cursor.close()
                response['status'] = 'success'
                response['message'] = 'Étudiant ajouté avec succès.'
                response['etudiant_id'] = etudiant_id
            else:
                cursor.close()
                response['status'] = 'error'
                response['message'] = "Promotion introuvable."



        elif action == 'add_note':
            note_data = request.get('data')
            etudiant_nom = note_data['etudiant_nom']
            etudiant_prenom = note_data['etudiant_prenom']
            valeur = note_data['valeur']
            coef = note_data['coef']
            cursor = connection.cursor()

            # Trouver l'ID de l'étudiant à partir du nom et prénom
            sql = "SELECT id FROM Etudiants WHERE nom = %s AND prenom = %s"
            cursor.execute(sql, (etudiant_nom, etudiant_prenom))
            results = cursor.fetchall()
            if len(results) == 1:
                etudiant_id = results[0][0]
                # Insérer la note
                sql = "INSERT INTO Notes (etudiant_id, valeur, coef) VALUES (%s, %s, %s)"
                cursor.execute(sql, (etudiant_id, valeur, coef))
                connection.commit()
                cursor.close()
                response['status'] = 'success'
                response['message'] = 'Note ajoutée avec succès.'
            elif len(results) == 0:
                cursor.close()
                response['status'] = 'error'
                response['message'] = "Étudiant introuvable."


        elif action == 'calculate_student_average':
            data = request.get('data')
            etudiant_nom = data.get('etudiant_nom')
            etudiant_prenom = data.get('etudiant_prenom')
            cursor = connection.cursor()

            # Trouver l'ID de l'étudiant
            sql = "SELECT id FROM Etudiants WHERE nom = %s AND prenom = %s"
            cursor.execute(sql, (etudiant_nom, etudiant_prenom))
            results = cursor.fetchall()
            if len(results) == 1:
                etudiant_id = results[0][0]
                # Calculer la moyenne
                sql = "SELECT valeur, coef FROM Notes WHERE etudiant_id = %s"
                cursor.execute(sql, (etudiant_id,))
                notes = cursor.fetchall()
                cursor.close()
                if notes:
                    total = sum(note[0] * note[1] for note in notes)
                    total_coef = sum(note[1] for note in notes)
                    moyenne = total / total_coef if total_coef != 0 else 0
                    response['status'] = 'success'
                    response['average'] = moyenne
                else:
                    response['status'] = 'error'
                    response['message'] = "Aucune note trouvée pour l'étudiant."
            elif len(results) == 0:
                cursor.close()
                response['status'] = 'error'
                response['message'] = "Étudiant introuvable."
            else:
                cursor.close()
                response['status'] = 'error'
                response['message'] = "Plusieurs étudiants trouvés avec ce nom et prénom."


        elif action == 'calculate_promotion_average':
            promo_nom = request.get('data').get('promo_nom')
            cursor = connection.cursor()
            # Trouver l'ID de la promotion
            sql = "SELECT id FROM Promotions WHERE nom = %s"
            cursor.execute(sql, (promo_nom,))
            result = cursor.fetchone()
            if result:
                promo_id = result[0]
                # Récupérer les étudiants de la promotion
                sql = "SELECT id FROM Etudiants WHERE promo_id = %s"
                cursor.execute(sql, (promo_id,))
                etudiants = cursor.fetchall()
                if etudiants:
                    moyennes = []
                    for etudiant in etudiants:
                        etudiant_id = etudiant[0]
                        sql_notes = "SELECT valeur, coef FROM Notes WHERE etudiant_id = %s"
                        cursor.execute(sql_notes, (etudiant_id,))
                        notes = cursor.fetchall()
                        if notes:
                            total = sum(note[0] * note[1] for note in notes)
                            total_coef = sum(note[1] for note in notes)
                            moyenne = total / total_coef if total_coef != 0 else 0
                            moyennes.append(moyenne)
                    cursor.close()
                    if moyennes:
                        moyenne_promo = sum(moyennes) / len(moyennes)
                        response['status'] = 'success'
                        response['average'] = moyenne_promo
                    else:
                        response['status'] = 'error'
                        response['message'] = "Aucune note trouvée pour les étudiants de la promotion."
                else:
                    cursor.close()
                    response['status'] = 'error'
                    response['message'] = "Aucun étudiant trouvé pour la promotion."
            else:
                cursor.close()
                response['status'] = 'error'
                response['message'] = "Promotion introuvable."


        elif action == 'get_student_details':
            data = request.get('data')
            etudiant_nom = data.get('etudiant_nom')
            etudiant_prenom = data.get('etudiant_prenom')
            cursor = connection.cursor(dictionary=True)

            sql = "SELECT * FROM Etudiants WHERE nom = %s AND prenom = %s"
            cursor.execute(sql, (etudiant_nom, etudiant_prenom))
            results = cursor.fetchall()
            if len(results) == 1:
                etudiant = results[0]
                etudiant_id = etudiant['id']
                sql_notes = "SELECT valeur, coef FROM Notes WHERE etudiant_id = %s"
                cursor.execute(sql_notes, (etudiant_id,))
                notes = cursor.fetchall()
                cursor.close()
                etudiant['notes'] = notes
                response['status'] = 'success'
                response['student'] = etudiant
            elif len(results) == 0:
                cursor.close()
                response['status'] = 'error'
                response['message'] = "Étudiant introuvable."
            else:
                cursor.close()
                response['status'] = 'error'
                response['message'] = "Plusieurs étudiants trouvés avec ce nom et prénom."


        else:
            response['status'] = 'error'
            response['message'] = 'Action inconnue.'

        # Envoyer la réponse au client
        client_socket.sendall(json.dumps(response).encode('utf-8'))

    except Error as e:
        print(f"Une erreur est survenue : {e}")
        error_response = {'status': 'error', 'message': str(e)}
        client_socket.sendall(json.dumps(error_response).encode('utf-8'))
    except Exception as e:
        print(f"Une erreur est survenue : {e}")
        error_response = {'status': 'error', 'message': str(e)}
        client_socket.sendall(json.dumps(error_response).encode('utf-8'))
    finally:
        if 'connection' in locals():
            connection.close()


# Boucle principale pour accepter les connexions entrantes
while True:
    client_socket, addr = server_socket.accept()
    client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
    client_thread.start()

