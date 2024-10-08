from dotenv import load_dotenv
import os
import socket
import threading
import mysql.connector
import json
import logging
from mysql.connector import Error

# Chargement des variables d'environnement
load_dotenv()
listening_ip = os.getenv('LISTENING_IP', '127.0.0.1')
listening_port = int(os.getenv('LISTENING_PORT', 12345))
db_host = os.getenv('DATABASE_HOST', 'localhost')
db_port = int(os.getenv('DATABASE_PORT', 3306))
db_user = os.getenv('DATABASE_USER', 'root')
db_password = os.getenv('DATABASE_PASSWORD', '')
db_name = os.getenv('DATABASE_NAME', 'mydatabase')
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
log_location = os.getenv('LOG_LOCATION')

# ==========Configuration du logging================================================
numeric_level = getattr(logging, log_level, None)
if not isinstance(numeric_level, int):
    raise ValueError(f"Niveau de log invalide : {log_level}")

logger = logging.getLogger(__name__)
logger.setLevel(numeric_level)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler(log_location, mode='a', encoding='utf-8')
file_handler.setLevel(numeric_level)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(numeric_level)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
# ===================================================================================

def get_db_connection():
    """Établit une connexion à la base de données."""
    return mysql.connector.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name
    )

# Création du serveur socket 
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((listening_ip, listening_port))
server_socket.listen()

logger.info(f"Serveur démarré et écoute sur {listening_ip}:{listening_port}")

# Gère la connexion avec un client.
def handle_client(client_socket, address):
    print(f"Connexion établie avec {address}")
    logger.info(f"Connexion établie avec {address}")
    try:
        handle_requests(client_socket, address)
    except Exception as e:
        logger.exception(f"Erreur lors du traitement des requêtes pour {address}: {e}")
    finally:
        client_socket.close()
        logger.info(f"Fermeture de la connexion avec {address}")

# Gère les requêtes envoyées par le client.
def handle_requests(client_socket, address):
    try:
        # Recevoir les données du client
        data = client_socket.recv(4096).decode('utf-8')
        if not data:
            return
        logger.debug(f"Reçu de {address} : {data}")
        request = json.loads(data)
        action = request.get('action')
        response = {}

        # Établir une connexion à la base de données pour ce thread
        connection = get_db_connection()
        logger.debug(f"Connexion à la base de données établie pour {address}")

        if action == 'create_promotion':
            promo_data = request.get('data')
            cursor = connection.cursor()
            sql = "INSERT INTO Promotions (nom) VALUES (%s)"
            logger.debug(f"Exécution de la requête SQL : {sql} avec les paramètres : {promo_data['nom']}")
            cursor.execute(sql, (promo_data['nom'],))
            connection.commit()
            promo_id = cursor.lastrowid
            cursor.close()
            response['status'] = 'success'
            response['message'] = f'Promotion {promo_data['nom']} créée avec succès.'
            response['promo_id'] = promo_id
            logger.info(f"Le client {address} a créé une promotion : {promo_data['nom']} (ID: {promo_id})")

        elif action == 'add_student':
            student_data = request.get('data')
            nom = student_data['nom']
            prenom = student_data['prenom']
            promo_nom = student_data['promo_nom']
            cursor = connection.cursor()

            # Trouver l'ID de la promotion à partir du nom
            sql = "SELECT id FROM Promotions WHERE nom = %s"
            logger.debug(f"Exécution de la requête SQL : {sql} avec les paramètres : {promo_nom}")
            cursor.execute(sql, (promo_nom,))
            result = cursor.fetchone()
            if result:
                promo_id = result[0]
                # Insérer l'étudiant
                sql = "INSERT INTO Etudiants (nom, prenom, promo_id) VALUES (%s, %s, %s)"
                logger.debug(f"Exécution de la requête SQL : {sql} avec les paramètres : {nom}, {prenom}, {promo_id}")
                cursor.execute(sql, (nom, prenom, promo_id))
                connection.commit()
                etudiant_id = cursor.lastrowid
                cursor.close()
                response['status'] = 'success'
                response['message'] = f'Étudiant {nom} {prenom} ajouté avec succès à la promotio {promo_nom}.'
                response['etudiant_id'] = etudiant_id
                logger.info(f"Le client {address} a ajouté un étudiant : {prenom} {nom} à la promotion {promo_nom} (ID Promotion: {promo_id}, ID Étudiant: {etudiant_id})")
            else:
                cursor.close()
                response['status'] = 'error'
                response['message'] = f"Promotion {promo_nom} introuvable."
                logger.error(f"Le client {address} a tenté d'ajouter un étudiant à une promotion introuvable : {promo_nom}")

        elif action == 'add_note':
            note_data = request.get('data')
            etudiant_nom = note_data['etudiant_nom']
            etudiant_prenom = note_data['etudiant_prenom']
            valeur = note_data['valeur']
            coef = note_data['coef']
            cursor = connection.cursor()

            # Trouver l'ID de l'étudiant à partir du nom et prénom
            sql = "SELECT id FROM Etudiants WHERE nom = %s AND prenom = %s"
            logger.debug(f"Exécution de la requête SQL : {sql} avec les paramètres : {etudiant_nom}, {etudiant_prenom}")
            cursor.execute(sql, (etudiant_nom, etudiant_prenom))
            results = cursor.fetchall()
            if len(results) == 1:
                etudiant_id = results[0][0]
                # Insérer la note
                sql = "INSERT INTO Notes (etudiant_id, valeur, coef) VALUES (%s, %s, %s)"
                logger.debug(f"Exécution de la requête SQL : {sql} avec les paramètres : {etudiant_id}, {valeur}, {coef}")
                cursor.execute(sql, (etudiant_id, valeur, coef))
                connection.commit()
                cursor.close()
                response['status'] = 'success'
                response['message'] = f'La note de {valeur} coef {coef} ajoutée avec succès à {etudiant_nom} {etudiant_prenom}.'
                logger.info(f"Le client {address} a ajouté une note pour {etudiant_prenom} {etudiant_nom} : valeur={valeur}, coef={coef}")
            elif len(results) == 0:
                cursor.close()
                response['status'] = 'error'
                response['message'] = f"Étudiant {etudiant_nom} {etudiant_prenom} introuvable."
                logger.error(f"Le client {address} a tenté d'ajouter une note à un étudiant introuvable : {etudiant_prenom} {etudiant_nom}")
            else:
                cursor.close()
                response['status'] = 'error'
                response['message'] = "Plusieurs étudiants trouvés avec ce nom et prénom. Veuillez préciser davantage."
                logger.warning(f"Le client {address} a trouvé plusieurs étudiants pour : {etudiant_prenom} {etudiant_nom}")

        elif action == 'calculate_student_average':
            data = request.get('data')
            etudiant_nom = data.get('etudiant_nom')
            etudiant_prenom = data.get('etudiant_prenom')
            cursor = connection.cursor()

            # Trouver l'ID de l'étudiant
            sql = "SELECT id FROM Etudiants WHERE nom = %s AND prenom = %s"
            logger.debug(f"Exécution de la requête SQL : {sql} avec les paramètres : {etudiant_nom}, {etudiant_prenom}")
            cursor.execute(sql, (etudiant_nom, etudiant_prenom))
            results = cursor.fetchall()
            if len(results) == 1:
                etudiant_id = results[0][0]
                # Calculer la moyenne
                sql = "SELECT valeur, coef FROM Notes WHERE etudiant_id = %s"
                logger.debug(f"Exécution de la requête SQL : {sql} avec les paramètres : {etudiant_id}")
                cursor.execute(sql, (etudiant_id,))
                notes = cursor.fetchall()
                cursor.close()
                if notes:
                    total = sum(note[0] * note[1] for note in notes)
                    total_coef = sum(note[1] for note in notes)
                    moyenne = total / total_coef if total_coef != 0 else 0
                    response['status'] = 'success'
                    response['message'] = f' La moyenne pour {etudiant_nom} {etudiant_prenom} est de {float(moyenne)}'
                    logger.info(f"Le client {address} a calculé la moyenne de {etudiant_prenom} {etudiant_nom} : moyenne={moyenne:.2f}")
                else:
                    response['status'] = 'error'
                    response['message'] = f"Aucune note trouvée pour l'étudiant {etudiant_nom} {etudiant_prenom}."
                    logger.warning(f"Aucune note trouvée pour {etudiant_prenom} {etudiant_nom}")
            elif len(results) == 0:
                cursor.close()
                response['status'] = 'error'
                response['message'] = "Étudiant introuvable."
                logger.error(f"Le client {address} a tenté de calculer la moyenne d'un étudiant introuvable : {etudiant_prenom} {etudiant_nom}")
            else:
                cursor.close()
                response['status'] = 'error'
                response['message'] = "Plusieurs étudiants trouvés avec ce nom et prénom."
                logger.warning(f"Plusieurs étudiants trouvés pour {etudiant_prenom} {etudiant_nom}")

        elif action == 'calculate_promotion_average':
            promo_nom = request.get('data').get('promo_nom')
            cursor = connection.cursor()
            # Trouver l'ID de la promotion
            sql = "SELECT id FROM Promotions WHERE nom = %s"
            logger.debug(f"Exécution de la requête SQL : {sql} avec les paramètres : {promo_nom}")
            cursor.execute(sql, (promo_nom,))
            result = cursor.fetchone()
            if result:
                promo_id = result[0]
                # Récupérer les étudiants de la promotion
                sql = "SELECT id FROM Etudiants WHERE promo_id = %s"
                logger.debug(f"Exécution de la requête SQL : {sql} avec les paramètres : {promo_id}")
                cursor.execute(sql, (promo_id,))
                etudiants = cursor.fetchall()
                if etudiants:
                    moyennes = []
                    for etudiant in etudiants:
                        etudiant_id = etudiant[0]
                        sql_notes = "SELECT valeur, coef FROM Notes WHERE etudiant_id = %s"
                        logger.debug(f"Exécution de la requête SQL : {sql_notes} avec les paramètres : {etudiant_id}")
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
                        response['message'] = f'La moyenne pour la promotion {promo_nom} est de {float(moyenne_promo)}'
                        logger.info(f"Le client {address} a calculé la moyenne de la promotion {promo_nom} : moyenne={moyenne_promo:.2f}")
                    else:
                        response['status'] = 'error'
                        response['message'] = f"Aucune note trouvée pour les étudiants de la promotion {promo_nom}."
                        logger.warning(f"Aucune note trouvée pour les étudiants de la promotion {promo_nom}")
                else:
                    cursor.close()
                    response['status'] = 'error'
                    response['message'] = f"Aucun étudiant trouvé dans la promotion {promo_nom}."
                    logger.warning(f"Aucun étudiant trouvé pour la promotion {promo_nom}")
            else:
                cursor.close()
                response['status'] = 'error'
                response['message'] = f"La promotion {promo_nom} n'existe pas."
                logger.error(f"Le client {address} a tenté de calculer la moyenne d'une promotion introuvable : {promo_nom}")

        elif action == 'get_student_details':
            data = request.get('data')
            etudiant_nom = data.get('etudiant_nom')
            etudiant_prenom = data.get('etudiant_prenom')
            cursor = connection.cursor(dictionary=True)

            sql = "SELECT * FROM Etudiants WHERE nom = %s AND prenom = %s"
            logger.debug(f"Exécution de la requête SQL : {sql} avec les paramètres : {etudiant_nom}, {etudiant_prenom}")
            cursor.execute(sql, (etudiant_nom, etudiant_prenom))
            results = cursor.fetchall()
            if len(results) == 1:
                etudiant = results[0]
                etudiant_id = etudiant['id']
                sql_notes = "SELECT valeur, coef FROM Notes WHERE etudiant_id = %s"
                logger.debug(f"Exécution de la requête SQL : {sql_notes} avec les paramètres : {etudiant_id}")
                cursor.execute(sql_notes, (etudiant_id,))
                notes = cursor.fetchall()
                cursor.close()
                etudiant['message'] = f"[{etudiant}]: {list(notes)}"
                response['status'] = 'success'
                logger.info(f"Le client {address} a récupéré les détails de {etudiant_prenom} {etudiant_nom}")
            elif len(results) == 0:
                cursor.close()
                response['status'] = 'error'
                response['message'] = f"Étudiant introuvable {etudiant_prenom} {etudiant_nom}."
                logger.error(f"Le client {address} a demandé les détails d'un étudiant introuvable : {etudiant_prenom} {etudiant_nom}")
            else:
                cursor.close()
                response['status'] = 'error'
                response['message'] = "Plusieurs étudiants trouvés avec ce nom et prénom."
                logger.warning(f"Plusieurs étudiants trouvés pour {etudiant_prenom} {etudiant_nom}")

        elif action == 'list_students_in_promotion':
            promo_nom = request.get('data').get('promo_nom')
            cursor = connection.cursor(dictionary=True)

            # Trouver l'ID de la promotion par son nom
            sql = "SELECT id FROM Promotions WHERE nom = %s"
            logger.debug(f"Exécution de la requête SQL : {sql} avec les paramètres : {promo_nom}")
            cursor.execute(sql, (promo_nom,))
            result = cursor.fetchone()

            if result:
                promo_id = result['id']
                # Obtenir la liste des étudiants dans la promotion
                sql = "SELECT nom, prenom FROM Etudiants WHERE promo_id = %s"
                logger.debug(f"Exécution de la requête SQL : {sql} avec les paramètres : {promo_id}")
                cursor.execute(sql, (promo_id,))
                students = cursor.fetchall()
                cursor.close()

                if students:
                    response['status'] = 'success'
                    response['students'] = list(students)
                    logger.info(f"Le client {address} a listé les étudiants de la promotion {promo_nom} ({len(students)} étudiants)")
                else:
                    response['status'] = 'error'
                    response['message'] = "Aucun étudiant trouvé dans la promotion."
                    logger.warning(f"Aucun étudiant trouvé dans la promotion {promo_nom}")
            else:
                cursor.close()
                response['status'] = 'error'
                response['message'] = "Promotion introuvable."
                logger.error(f"Le client {address} a demandé une liste d'étudiants pour une promotion introuvable : {promo_nom}")

        elif action == 'handshake':
            response['status'] = 'success'
            response['message'] = 'You connected to me'
            logger.info(f"Le client {address} vient d'effectuer un test de connexion")
        
        else:
            response['status'] = 'error'
            response['message'] = 'Action inconnue.'
            logger.warning(f"Action inconnue reçue de {address}: {action}")

        # Envoyer la réponse au client
        client_socket.sendall(json.dumps(response).encode('utf-8'))
        logger.debug(f"Réponse envoyée à {address} : {response}")
    except Error as e:
        logger.exception(f"Une erreur MySQL est survenue avec {address}: {e}")
        error_response = {'status': 'error', 'message': str(e)}
        client_socket.sendall(json.dumps(error_response).encode('utf-8'))
    except Exception as e:
        logger.exception(f"Une erreur est survenue avec {address}: {e}")
        error_response = {'status': 'error', 'message': str(e)}
        client_socket.sendall(json.dumps(error_response).encode('utf-8'))
    finally:
        if 'connection' in locals():
            logger.debug(f"Fermeture de la connexion à la base de données pour {address}")
            connection.close()

# Boucle principale pour accepter les connexions entrantes
while True:
    client_socket, addr = server_socket.accept()
    client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
    client_thread.start()
