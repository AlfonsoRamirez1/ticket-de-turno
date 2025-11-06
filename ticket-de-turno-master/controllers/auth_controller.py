# controllers/auth_controller.py
from db import db
from models.db_models import Administradores
from flask_bcrypt import Bcrypt
from sqlalchemy.exc import SQLAlchemyError

class AuthController:

    def __init__(self):
        # bcrypt se puede inicializar sin la app
        # se vinculará cuando la app se cree
        self.bcrypt = Bcrypt()

    def validar_login(self, usuario, password_ingresada):
        """
        Valida las credenciales del usuario usando el ORM.
        Retorna un objeto Administradores si es exitoso, None si falla.
        """
        try:
            # db.session.scalar() es la forma moderna de obtener un solo objeto
            admin = db.session.scalar(
                db.select(Administradores).where(Administradores.usuario == usuario)
            )

            if admin and self.bcrypt.check_password_hash(admin.password, password_ingresada):
                return admin # Retorna el objeto ORM

            return None  # Usuario no encontrado o contraseña incorrecta

        except SQLAlchemyError as e:
            print(f"Error en BD al validar login: {e}")
            return None

    def get_user_by_id(self, user_id):
        """
        Obtiene un usuario por su ID. Requerido por flask-login.
        """
        try:
            # db.session.get() es la forma más rápida de obtener por Primary Key
            return db.session.get(Administradores, int(user_id))
        except SQLAlchemyError as e:
            print(f"Error en BD en get_user_by_id: {e}")
            return None