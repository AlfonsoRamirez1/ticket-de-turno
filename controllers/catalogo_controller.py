# controllers/catalogo_controller.py
from DB.db import db
from models.db_models import Municipios, NivelesEducativos, Asuntos, OficinasRegionales, HorariosAtencion
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import time


class CatalogoController:

    def __init__(self):
        pass  # Ya no necesitamos self.db

    # --- Métodos para MUNICIPIOS ---

    def get_municipios(self):
        """ Obtiene todos los municipios (como objetos ORM). """
        # .scalars() obtiene los objetos del modelo, .all() los pone en una lista
        return db.session.scalars(
            db.select(Municipios).order_by(Municipios.municipio)
        ).all()

    def get_municipio_by_id(self, id_municipio):
        """ Obtiene un municipio específico por su ID. """
        return db.session.get(Municipios, id_municipio)

    def crear_municipio(self, municipio_nombre):
        """ Crea un nuevo municipio. """
        if not municipio_nombre:
            return False, "El nombre no puede estar vacío."

        nuevo_municipio = Municipios(municipio=municipio_nombre)
        db.session.add(nuevo_municipio)

        try:
            db.session.commit()
            return True, "Municipio creado con éxito."
        except IntegrityError as e:
            db.session.rollback()
            if "UNIQUE constraint failed" in str(e) or "Duplicate entry" in str(e):
                return False, f"El municipio '{municipio_nombre}' ya existe."
            return False, f"Error de integridad al crear: {e}"
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, f"Error de base de datos al crear: {e}"

    def actualizar_municipio(self, id_municipio, municipio_nombre):
        """ Actualiza el nombre de un municipio. """
        if not municipio_nombre:
            return False, "El nombre no puede estar vacío."

        municipio = db.session.get(Municipios, id_municipio)
        if not municipio:
            return False, "Municipio no encontrado."

        municipio.municipio = municipio_nombre
        try:
            db.session.commit()
            return True, "Municipio actualizado con éxito."
        except IntegrityError as e:
            db.session.rollback()
            return False, f"El nombre '{municipio_nombre}' ya existe."
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, f"Error de base de datos al actualizar: {e}"

    def eliminar_municipio(self, id_municipio):
        """ Elimina un municipio. """
        municipio = db.session.get(Municipios, id_municipio)
        if not municipio:
            return False, "Municipio no encontrado."

        db.session.delete(municipio)
        try:
            db.session.commit()
            return True, "Municipio eliminado con éxito."
        except IntegrityError as e:
            db.session.rollback()
            # Error 1451: Foreign Key constraint
            if "FOREIGN KEY constraint" in str(e):
                return False, "No se puede eliminar: el municipio está siendo usado por una oficina."
            return False, f"Error de integridad: {e}"
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, f"Error de base de datos al eliminar: {e}"

    # --- Métodos para NIVELES EDUCATIVOS (siguen el mismo patrón) ---

    def get_niveles(self):
        return db.session.scalars(
            db.select(NivelesEducativos).order_by(NivelesEducativos.id_nivel)
        ).all()

    def get_nivel_by_id(self, id_nivel):
        return db.session.get(NivelesEducativos, id_nivel)

    def crear_nivel(self, nivel_nombre):
        if not nivel_nombre: return False, "El nombre no puede estar vacío."
        nuevo = NivelesEducativos(nivel=nivel_nombre)
        db.session.add(nuevo)
        try:
            db.session.commit()
            return True, "Nivel creado con éxito."
        except IntegrityError:
            db.session.rollback()
            return False, f"El nivel '{nivel_nombre}' ya existe."
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, f"Error al crear: {e}"

    def actualizar_nivel(self, id_nivel, nivel_nombre):
        if not nivel_nombre: return False, "El nombre no puede estar vacío."
        nivel_obj = db.session.get(NivelesEducativos, id_nivel)
        if not nivel_obj: return False, "Nivel no encontrado."
        nivel_obj.nivel = nivel_nombre
        try:
            db.session.commit()
            return True, "Nivel actualizado con éxito."
        except IntegrityError:
            db.session.rollback()
            return False, f"El nivel '{nivel_nombre}' ya existe."
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, f"Error al actualizar: {e}"

    def eliminar_nivel(self, id_nivel):
        nivel_obj = db.session.get(NivelesEducativos, id_nivel)
        if not nivel_obj: return False, "Nivel no encontrado."
        db.session.delete(nivel_obj)
        try:
            db.session.commit()
            return True, "Nivel eliminado con éxito."
        except IntegrityError:
            db.session.rollback()
            return False, "No se puede eliminar: el nivel está siendo usado por un turno."
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, f"Error al eliminar: {e}"

    # --- Métodos para ASUNTOS (siguen el mismo patrón) ---

    def get_asuntos(self):
        return db.session.scalars(
            db.select(Asuntos).order_by(Asuntos.descripcion)
        ).all()

    def get_asunto_by_id(self, id_asunto):
        return db.session.get(Asuntos, id_asunto)

    def crear_asunto(self, descripcion):
        if not descripcion: return False, "La descripción no puede estar vacía."
        nuevo = Asuntos(descripcion=descripcion)
        db.session.add(nuevo)
        try:
            db.session.commit()
            return True, "Asunto creado con éxito."
        except IntegrityError:
            db.session.rollback()
            return False, f"El asunto '{descripcion}' ya existe."
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, f"Error al crear: {e}"

    def actualizar_asunto(self, id_asunto, descripcion):
        if not descripcion: return False, "La descripción no puede estar vacía."
        asunto_obj = db.session.get(Asuntos, id_asunto)
        if not asunto_obj: return False, "Asunto no encontrado."
        asunto_obj.descripcion = descripcion
        try:
            db.session.commit()
            return True, "Asunto actualizado con éxito."
        except IntegrityError:
            db.session.rollback()
            return False, f"El asunto '{descripcion}' ya existe."
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, f"Error al actualizar: {e}"

    def eliminar_asunto(self, id_asunto):
        asunto_obj = db.session.get(Asuntos, id_asunto)
        if not asunto_obj: return False, "Asunto no encontrado."
        db.session.delete(asunto_obj)
        try:
            db.session.commit()
            return True, "Asunto eliminado con éxito."
        except IntegrityError:
            db.session.rollback()
            return False, "No se puede eliminar: el asunto está siendo usado por un turno."
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, f"Error al eliminar: {e}"

    # --- Métodos para OFICINAS REGIONALES (siguen el mismo patrón) ---

    def get_oficinas(self):
        # Usamos joinedload para traer el nombre del municipio en la misma consulta
        return db.session.scalars(
            db.select(OficinasRegionales)
            .options(db.joinedload(OficinasRegionales.municipio))
            .order_by(OficinasRegionales.oficina)
        ).all()

    def get_oficina_by_id(self, id_oficina):
        return db.session.get(OficinasRegionales, id_oficina)

    def crear_oficina(self, oficina_nombre, id_municipio):
        if not oficina_nombre or not id_municipio:
            return False, "El nombre y el municipio son obligatorios."
        nuevo = OficinasRegionales(oficina=oficina_nombre, id_municipio=id_municipio)
        db.session.add(nuevo)
        try:
            db.session.commit()
            return True, "Oficina creada con éxito."
        except IntegrityError as e:
            db.session.rollback()
            return False, "Error de clave foránea. ¿El municipio existe?"
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, f"Error al crear: {e}"

    def actualizar_oficina(self, id_oficina, oficina_nombre, id_municipio):
        if not oficina_nombre or not id_municipio:
            return False, "El nombre y el municipio son obligatorios."
        oficina_obj = db.session.get(OficinasRegionales, id_oficina)
        if not oficina_obj: return False, "Oficina no encontrada."

        oficina_obj.oficina = oficina_nombre
        oficina_obj.id_municipio = id_municipio
        try:
            db.session.commit()
            return True, "Oficina actualizada con éxito."
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, f"Error al actualizar: {e}"

    def eliminar_oficina(self, id_oficina):
        oficina_obj = db.session.get(OficinasRegionales, id_oficina)
        if not oficina_obj: return False, "Oficina no encontrada."
        db.session.delete(oficina_obj)
        try:
            db.session.commit()
            return True, "Oficina eliminada con éxito."
        except IntegrityError:
            db.session.rollback()
            return False, "No se puede eliminar: la oficina está siendo usada por un turno."
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, f"Error al eliminar: {e}"

    # --- Métodos para HORARIOS DE ATENCIÓN (ACTUALIZADOS) ---

    def get_horarios(self):
        """ Obtiene todos los horarios, uniéndolos con sus oficinas. """
        return db.session.scalars(
            db.select(HorariosAtencion)
            .options(db.joinedload(HorariosAtencion.oficina))
            .order_by(HorariosAtencion.id_oficina, HorariosAtencion.dia_semana)
        ).all()

    def get_horario_by_id(self, id_horario):
        """ Obtiene un horario específico por su ID. """
        return db.session.get(HorariosAtencion, id_horario)

    def crear_horario(self, form_data):
        """ Crea uno o más horarios de atención (batch). """
        # Obtenemos la LISTA de checkboxes seleccionados
        dias_seleccionados = form_data.getlist('dias_semana')
        id_oficina = form_data.get('id_oficina')

        if not dias_seleccionados:
            return False, "Debe seleccionar al menos un día de la semana."

        try:
            # Extraer los datos comunes una sola vez
            hora_apertura = time.fromisoformat(form_data.get('hora_apertura'))
            hora_cierre = time.fromisoformat(form_data.get('hora_cierre'))
            max_turnos_dia = form_data.get('max_turnos_dia')

            # Iteramos sobre la lista de días y creamos un objeto por cada uno
            for dia in dias_seleccionados:
                nuevo_horario = HorariosAtencion(
                    id_oficina=id_oficina,
                    dia_semana=dia,
                    hora_apertura=hora_apertura,
                    hora_cierre=hora_cierre,
                    max_turnos_dia=max_turnos_dia
                )
                db.session.add(nuevo_horario)

            # Hacemos commit una sola vez al final del bucle
            db.session.commit()

            # Mensaje de éxito
            num_dias = len(dias_seleccionados)
            plural = "s" if num_dias > 1 else ""
            return True, f"{num_dias} horario{plural} creado{plural} con éxito."

        except IntegrityError:
            db.session.rollback()
            return False, "Error: Uno o más de esos horarios ya existen para esa oficina."
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, f"Error de base de datos al crear: {e}"
        except Exception as e:
            db.session.rollback()
            return False, f"Error inesperado: {e}"

    def actualizar_horario(self, form_data):
        """ Actualiza un horario de atención. """
        try:
            id_horario = form_data.get('id_horario')
            horario = db.session.get(HorariosAtencion, id_horario)
            if not horario:
                return False, "Horario no encontrado."

            horario.id_oficina = form_data.get('id_oficina')
            horario.dia_semana = form_data.get('dia_semana')
            horario.hora_apertura = time.fromisoformat(form_data.get('hora_apertura'))
            horario.hora_cierre = time.fromisoformat(form_data.get('hora_cierre'))
            horario.max_turnos_dia = form_data.get('max_turnos_dia')

            db.session.commit()
            return True, "Horario actualizado con éxito."
        except IntegrityError:
            db.session.rollback()
            return False, "Error: Ya existe un horario para esa oficina en ese día."
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, f"Error de base de datos al actualizar: {e}"

    def eliminar_horario(self, id_horario):
        """ Elimina un horario de atención. """
        horario = db.session.get(HorariosAtencion, id_horario)
        if not horario:
            return False, "Horario no encontrado."

        db.session.delete(horario)
        try:
            db.session.commit()
            return True, "Horario eliminado con éxito."
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, f"Error de base de datos al eliminar: {e}"