# controllers/catalogo_controller.py
from DB.db import Database
import pymysql # Necesario para capturar errores de BD

class CatalogoController:

    def __init__(self):
        self.db = Database()

    # --- Métodos para MUNICIPIOS ---

    def get_municipios(self):
        """ Obtiene todos los municipios para la tabla de admin. """
        return self.db.fetchall("SELECT * FROM municipios ORDER BY municipio")

    def get_municipio_by_id(self, id_municipio):
        """ Obtiene un municipio específico por su ID. """
        return self.db.fetchone("SELECT * FROM municipios WHERE id_municipio = %s", (id_municipio,))

    def crear_municipio(self, municipio_nombre):
        """ Crea un nuevo municipio. """
        if not municipio_nombre:
            return False, "El nombre no puede estar vacío."
        try:
            sql = "INSERT INTO municipios (municipio) VALUES (%s)"
            self.db.execute(sql, (municipio_nombre,), commit=True)
            return True, "Municipio creado con éxito."
        except pymysql.MySQLError as e:
            # Captura un error si el municipio ya existe (UNIQUE)
            if e.args[0] == 1062: # Código de error para 'Entrada duplicada'
                return False, f"El municipio '{municipio_nombre}' ya existe."
            return False, f"Error al crear: {e}"

    def actualizar_municipio(self, id_municipio, municipio_nombre):
        """ Actualiza el nombre de un municipio. """
        if not municipio_nombre:
            return False, "El nombre no puede estar vacío."
        try:
            sql = "UPDATE municipios SET municipio = %s WHERE id_municipio = %s"
            self.db.execute(sql, (municipio_nombre, id_municipio), commit=True)
            return True, "Municipio actualizado con éxito."
        except pymysql.MySQLError as e:
            if e.args[0] == 1062:
                return False, f"El municipio '{municipio_nombre}' ya existe."
            return False, f"Error al actualizar: {e}"

    def eliminar_municipio(self, id_municipio):
        """ Elimina un municipio. """
        try:
            sql = "DELETE FROM municipios WHERE id_municipio = %s"
            self.db.execute(sql, (id_municipio,), commit=True)
            return True, "Municipio eliminado con éxito."
        except pymysql.MySQLError as e:
            # Captura error si el municipio está en uso (FOREIGN KEY)
            if e.args[0] == 1451: # Código de error para 'Foreign Key constraint'
                return False, "No se puede eliminar: el municipio está siendo usado por una oficina o un turno."
            return False, f"Error al eliminar: {e}"

    # --- Aquí irán los métodos para Asuntos, Niveles y Oficinas ---