import os
import firebase_admin
from firebase_admin import credentials, firestore

def inicializar_firebase():
    if not firebase_admin._apps:
        caminho_credencial = os.path.join(os.path.dirname(__file__), 'reserva-salas-bb922-firebase-adminsdk-fbsvc-e85e81c08e.json')
        cred = credentials.Certificate(caminho_credencial)
        firebase_admin.initialize_app(cred)

    return firestore.client()
