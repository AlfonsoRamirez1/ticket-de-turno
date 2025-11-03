# models/turno.py
from datetime import datetime


class Turno:
    def __init__(self, id_turno=None, id_solicitante=None, id_oficina=None,
                 numero_turno=None, id_nivel=None, id_asunto=None,
                 estado='pendiente', codigo_qr=None, fecha_solicitud=None, solicitante=None):
        self.id_turno = id_turno
        self.id_solicitante = id_solicitante
        self.id_oficina = id_oficina  # Lo obtendremos del municipio
        self.numero_turno = numero_turno
        self.id_nivel = id_nivel
        self.id_asunto = id_asunto
        self.estado = estado  # Valor por defecto 'pendiente' [cite: 80]
        self.codigo_qr = codigo_qr  # Lo generaremos más adelante (Req. 6)
        self.fecha_solicitud = fecha_solicitud or datetime.now()

        # Este atributo contendrá el objeto Solicitante asociado
        self.solicitante = solicitante

    @staticmethod
    def from_form(form_data):
        # Crea un objeto Turno desde los datos del formulario
        return Turno(
            id_oficina=form_data.get('oficina'),  # Necesitaremos un select de oficinas
            id_nivel=form_data.get('nivel'),
            id_asunto=form_data.get('asunto')
        )