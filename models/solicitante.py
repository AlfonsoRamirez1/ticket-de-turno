# models/solicitante.py
class Solicitante:
    def __init__(self, id_solicitante=None, nombre_tramitante=None, nombre_solicitante=None,
                 paterno_solicitante=None, materno_solicitante=None, curp=None,
                 telefono=None, celular=None, correo=None):
        self.id_solicitante = id_solicitante
        self.nombre_tramitante = nombre_tramitante     # Corresponde a 'nombreCompleto' del form
        self.nombre_solicitante = nombre_solicitante    # Corresponde a 'nombre' del form
        self.paterno_solicitante = paterno_solicitante  # Corresponde a 'paterno' del form
        self.materno_solicitante = materno_solicitante  # Corresponde a 'materno' del form
        self.curp = curp
        self.telefono = telefono
        self.celular = celular
        self.correo = correo

    @staticmethod
    def from_form(form_data):
        # Crea un objeto Solicitante desde los datos del formulario
        return Solicitante(
            nombre_tramitante=form_data.get('nombreCompleto'),
            nombre_solicitante=form_data.get('nombre'),
            paterno_solicitante=form_data.get('paterno'),
            materno_solicitante=form_data.get('materno'),
            curp=form_data.get('curp'),
            telefono=form_data.get('telefono'),
            celular=form_data.get('celular'),
            correo=form_data.get('correo')
        )