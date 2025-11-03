# models/admin.py
from flask_login import UserMixin

class Admin(UserMixin):
    """
    Modelo para la tabla 'administradores' de la base de datos.
    UserMixin proporciona implementaciones para métodos que flask-login espera
    (is_authenticated, is_active, is_anonymous, get_id).
    """
    def __init__(self, id_admin, usuario, password, rol, nombre, **kwargs):
        """
        Constructor actualizado para aceptar 'nombre' y cualquier
        otro campo de la BD (gracias a **kwargs).
        """
        self.id = id_admin # flask-login espera un atributo 'id'
        self.id_admin = id_admin
        self.usuario = usuario
        self.password = password
        self.rol = rol
        self.nombre = nombre # <-- ¡LA LÍNEA QUE FALTABA!