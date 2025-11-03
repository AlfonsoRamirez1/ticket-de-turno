# create_admin.py
from getpass import getpass
from flask_bcrypt import Bcrypt
from DB.db import Database  # Usamos tu clase de BD [cite: 58-69]


def crear_admin_inicial():
    db = Database()
    bcrypt = Bcrypt()
    conn = None

    print("--- Creación de Administrador Inicial ---")
    usuario = input("Ingrese el nombre de usuario: ")
    password = getpass("Ingrese la contraseña: ")
    rol = "admin"  # O 'usuario' según tu tabla

    # Hashear la contraseña
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    try:
        conn = db.conectar()
        with conn.cursor() as cur:
            sql = """
                  INSERT INTO administradores (usuario, password, nombre, rol)
                  VALUES (%s, %s, %s, %s) \
                  """
            cur.execute(sql, (usuario, hashed_password, "Admin Principal", rol))
            conn.commit()
            print(f"✅ Administrador '{usuario}' creado exitosamente.")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Error al crear administrador: {e}")
    finally:
        if conn:
            db.desconectar()


if __name__ == "__main__":
    crear_admin_inicial()