# DB/db.py
import pymysql
from config import Config

class Database:
    def __init__(self):
        self.connection = None

    def conectar(self):
        if self.connection and self.connection.open:
            return self.connection
        try:
            self.connection = pymysql.connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASS,
                database=Config.DB_NAME,
                port=int(Config.DB_PORT),
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
            print("✅ Conexión exitosa a la base de datos.")
            return self.connection
        except Exception as e:
            print(f"❌ Error al conectar a la base de datos: {e}")
            raise

    def desconectar(self):
        """Cierra la conexión."""
        try:
            if self.connection and self.connection.open:
                self.connection.close()
                print("🔌 Conexión cerrada correctamente.")
        except Exception as e:
            print(f"⚠️ Error al cerrar conexión: {e}")
            raise

    def execute(self, query, params=None, commit=False):
        """Ejecuta una consulta (INSERT, UPDATE, DELETE)."""
        conn = self.conectar()
        with conn.cursor() as cursor:
            try:
                cursor.execute(query, params)
                if commit:
                    conn.commit()
                return cursor
            except Exception as e:
                conn.rollback()
                print(f"❌ Error al ejecutar query: {e}")
                raise

    def fetchall(self, query, params=None):
        """Ejecuta un SELECT y devuelve todos los registros."""
        conn = self.conectar()
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def fetchone(self, query, params=None):
        """Ejecuta un SELECT y devuelve un solo registro."""
        conn = self.conectar()
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()
