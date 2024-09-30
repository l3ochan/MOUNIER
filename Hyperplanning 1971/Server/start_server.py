from dotenv import load_dotenv
import os

load_dotenv()
listening_ip = os.getenv('LISTENING_IP')
listening_port = int(os.getenv('LISTENING_PORT'))


