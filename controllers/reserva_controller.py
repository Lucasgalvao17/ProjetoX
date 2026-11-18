from utils.firebase_utils import inicializar_firebase
from models.reserva_model import Reserva

db = inicializar_firebase()
COLLECTION_NAME = "reservas"

class ReservaController:

    @staticmethod
    def criar_reserva(reserva: Reserva):
        # Adiciona uma nova reserva no Firestore
        doc_ref = db.collection(COLLECTION_NAME).document()
        doc_ref.set(reserva.to_dict())
        return doc_ref.id

    @staticmethod
    def listar_reservas():
        # Busca todas as reservas cadastradas no Firestore
        docs = db.collection(COLLECTION_NAME).stream()
        reservas = []
        for doc in docs:
            reservas.append(Reserva.from_dict(doc.id, doc.to_dict()))
        return reservas

    @staticmethod
    def atualizar_reserva(id, reserva: Reserva):
        # Atualiza os dados de uma reserva existente
        doc_ref = db.collection(COLLECTION_NAME).document(id)
        doc_ref.update(reserva.to_dict())

    @staticmethod
    def deletar_reserva(id):
        # Remove uma reserva pelo ID
        db.collection(COLLECTION_NAME).document(id).delete()
