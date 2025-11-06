# create_admin.py
from getpass import getpass
from flask import Flask
from flask_bcrypt import Bcrypt
from db import db  # Importamos la instancia de BD
from models.db_models import Administradores  # Importamos el modelo
from config import Config
from sqlalchemy.exc import IntegrityError


def crear_admin_inicial():
    # Creamos una app temporal solo para este script
    temp_app = Flask(__name__)
    temp_app.config.from_object(Config)

    # Inicializamos la BD y Bcrypt con esta app
    db.init_app(temp_app)
    bcrypt = Bcrypt(temp_app)

    print("--- Creación de Administrador Inicial (ORM) ---")
    usuario = input("Ingrese el nombre de usuario: ")
    password = getpass("Ingrese la contraseña: ")
    nombre = input("Ingrese el nombre completo del admin: ")
    rol = "admin"

    # Hashear la contraseña
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Usamos el app_context de la app temporal
    with temp_app.app_context():
        try:
            # Creamos el objeto ORM
            nuevo_admin = Administradores(
                usuario=usuario,
                password=hashed_password,
                nombre=nombre,
                rol=rol
            )

            db.session.add(nuevo_admin)
            db.session.commit()
            print(f"✅ Administrador '{usuario}' creado exitosamente.")

        except IntegrityError:
            db.session.rollback()
            print(f"❌ Error: El usuario '{usuario}' ya existe.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al crear administrador: {e}")


if __name__ == "__main__":
    crear_admin_inicial()