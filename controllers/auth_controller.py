# controllers/auth_controller.py
from DB.db import Database
from models.admin import Admin
from flask_bcrypt import Bcrypt


class AuthController:

    def __init__(self):
        self.db = Database()
        self.bcrypt = Bcrypt()  # Para comparar contraseñas

    def validar_login(self, usuario, password_ingresada):
        """
        Valida las credenciales del usuario.
        Retorna un objeto Admin si es exitoso, None si falla.
        """
        conn = None
        try:
            conn = self.db.conectar()
            with conn.cursor() as cur:
                # Busca en la tabla 'administradores'
                sql = "SELECT * FROM administradores WHERE usuario = %s"
                cur.execute(sql, (usuario,))
                user_data = cur.fetchone()

                if user_data:
                    # Compara la contraseña hasheada de la BD
                    # con la contraseña ingresada por el usuario
                    password_hash = user_data['password']
                    if self.bcrypt.check_password_hash(password_hash, password_ingresada):
                        # ¡Éxito! Retorna un objeto Admin
                        return Admin(**user_data)

            return None  # Usuario no encontrado o contraseña incorrecta

        except Exception as e:
            print(f"Error al validar login: {e}")
            return None
        finally:
            if conn:
                self.db.desconectar()

    def get_user_by_id(self, user_id):
        """
        Obtiene un usuario por su ID. Requerido por flask-login.
        """
        conn = None
        try:
            conn = self.db.conectar()
            with conn.cursor() as cur:
                sql = "SELECT * FROM administradores WHERE id_admin = %s"
                cur.execute(sql, (user_id,))
                user_data = cur.fetchone()

                if user_data:
                    return Admin(**user_data)  # Retorna objeto Admin
            return None

        except Exception as e:
            print(f"Error en get_user_by_id: {e}")
            return None
        finally:
            if conn:
                self.db.desconectar()