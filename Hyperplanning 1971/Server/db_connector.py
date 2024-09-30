from dotenv import load_dotenv
import os
import mysql.connector
from mysql.connector import Error

db_host = os.getenv('DATABASE_HOST')
db_port = int(os.getenv('DATABASE_PORT'))
db_user = os.getenv('DATABASE_USER')
db_password = os.getenv('DATABASE_PASSWORD')
db_name = os.getenv('DATABASE_NAME')

def create_connection(host_name, user_name, user_password, db_name):
    connection = None
    try:
        connection = mysql.connector.connect(
            host = db_host,
            user = db_user,
            password = db_password,
            database = db_name
            port = db_port
        )
        print("Connexion réussie à la base de données")
    except Error as e:
        print(f"L'erreur '{e}' est survenue")
    return connection


# Créer la connexion
conn = create_connection(db_host, db_user, db_password, db_name, db_port)

# N'oubliez pas de fermer la connexion après avoir effectué des opérations
if conn:
    conn.close()