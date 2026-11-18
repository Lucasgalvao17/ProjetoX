class Reserva:
    def __init__(self, sala, data, horario_inicio, horario_fim, responsavel, finalidade="", id=None):
        self.id = id
        self.sala = sala
        self.data = data
        self.horario_inicio = horario_inicio
        self.horario_fim = horario_fim
        self.responsavel = responsavel
        self.finalidade = finalidade

    def to_dict(self):
        # Converte o objeto Reserva em um dicionário para salvar no Firestore
        return {
            "sala": self.sala,
            "data": str(self.data),
            "horario_inicio": str(self.horario_inicio),
            "horario_fim": str(self.horario_fim),
            "responsavel": self.responsavel,
            "finalidade": self.finalidade
        }

    @staticmethod
    def from_dict(id, data_dict):
        # Converte um documento vindo do Firestore de volta para um objeto Reserva
        return Reserva(
            id=id,
            sala=data_dict.get("sala", ""),
            data=data_dict.get("data", ""),
            horario_inicio=data_dict.get("horario_inicio", ""),
            horario_fim=data_dict.get("horario_fim", ""),
            responsavel=data_dict.get("responsavel", ""),
            finalidade=data_dict.get("finalidade", "")
        )
