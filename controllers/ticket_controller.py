# controllers/ticket_controller.py
from DB.db import db
from models.db_models import (
    Turnos, Solicitantes, Municipios, NivelesEducativos,
    Asuntos, OficinasRegionales, ContadorTurnos, HorariosAtencion
)
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import or_, func, and_  # Para búsquedas OR, funciones SQL y AND
from datetime import datetime, timedelta, time

# --- DICCIONARIO PARA MAPEAR DÍAS ---
DIAS_SEMANA_ES = {
    0: 'lunes',
    1: 'martes',
    2: 'miercoles',
    3: 'jueves',
    4: 'viernes',
    5: 'sabado',
    6: 'domingo'
}
SLOT_DURATION_MINUTES = 30


class TicketController:

    def __init__(self):
        pass  # Ya no necesitamos self.db

    # --- NUEVOS MÉTODOS PRIVADOS PARA LÓGICA DE HORARIOS ---

    def _round_up_time(self, dt, minutes_res):
        """ Redondea un datetime.datetime hacia arriba al próximo intervalo. """
        min_dt = datetime.min.time()
        delta = datetime.combine(dt.date(), dt.time()) - datetime.combine(dt.date(), min_dt)
        minutes = (delta.seconds // 60 + minutes_res - 1) // minutes_res * minutes_res
        return datetime.combine(dt.date(), min_dt) + timedelta(minutes=minutes)

    def _get_dia_semana_es(self, date_obj):
        """ Obtiene el nombre del día en español a partir de un objeto date. """
        return DIAS_SEMANA_ES[date_obj.weekday()]

    def _encontrar_proximo_horario(self, id_oficina):
        """
        Encuentra el próximo slot de cita disponible para una oficina.
        Retorna (fecha_cita, hora_cita) o (None, None)
        """
        ahora = datetime.now()
        inicio_busqueda = self._round_up_time(ahora, SLOT_DURATION_MINUTES)

        for i in range(30):
            fecha_a_revisar = (inicio_busqueda + timedelta(days=i)).date()
            dia_semana = self._get_dia_semana_es(fecha_a_revisar)

            horario_db = db.session.scalar(
                db.select(HorariosAtencion).where(
                    HorariosAtencion.id_oficina == id_oficina,
                    HorariosAtencion.dia_semana == dia_semana
                )
            )

            if not horario_db:
                continue

            max_turnos_hoy = horario_db.max_turnos_dia
            turnos_hoy_count = db.session.scalar(
                db.select(func.count(Turnos.id_turno)).where(
                    Turnos.id_oficina == id_oficina,
                    func.date(Turnos.fecha_solicitud) == fecha_a_revisar
                )
            )

            if turnos_hoy_count >= max_turnos_hoy:
                continue

            # --- INICIO DE CORRECCIÓN (BUGS DE HORA DE INICIO) ---

            hora_apertura_oficina = horario_db.hora_apertura
            hora_cierre_dt = datetime.combine(fecha_a_revisar, horario_db.hora_cierre)
            hora_cierre_limite = (hora_cierre_dt - timedelta(minutes=SLOT_DURATION_MINUTES)).time()

            if fecha_a_revisar == ahora.date():
                # Si es hoy, empezamos desde la hora redondeada (ej. 13:00)
                hora_inicio_busqueda = inicio_busqueda.time()

                # FIX 1: Nos aseguramos de no empezar ANTES de la hora de apertura
                # Usamos el máximo entre la hora de apertura y la hora redondeada
                hora_inicio_slots = max(hora_inicio_busqueda, hora_apertura_oficina)
            else:
                # Si es un día futuro, empezamos a la hora de apertura
                hora_inicio_slots = hora_apertura_oficina

            # FIX 2: Verificar si ya es demasiado tarde para buscar slots HOY.
            # Si la hora de inicio (ej: 15:00) ya superó el último slot (ej: 14:30),
            # saltamos a mañana.
            if hora_inicio_slots > hora_cierre_limite:
                continue  # Saltar al siguiente día (loop 'for i in range(30)')

            # --- FIN DE CORRECCIÓN ---

            slot_actual_dt = datetime.combine(fecha_a_revisar, hora_inicio_slots)

            while slot_actual_dt.time() <= hora_cierre_limite:
                slot_time = slot_actual_dt.time()

                slot_ocupado = db.session.scalar(
                    db.select(Turnos.id_turno).where(
                        Turnos.id_oficina == id_oficina,
                        func.date(Turnos.fecha_solicitud) == fecha_a_revisar,
                        Turnos.hora_solicitud == slot_time
                    )
                )

                if not slot_ocupado:
                    return (fecha_a_revisar, slot_time)

                slot_actual_dt += timedelta(minutes=SLOT_DURATION_MINUTES)

        return (None, None)

    # --- MÉTODOS PARA OBTENER CATÁLOGOS ---
    def obtener_municipios(self):
        return db.session.scalars(db.select(Municipios).order_by(Municipios.municipio)).all()

    def obtener_niveles(self):
        return db.session.scalars(db.select(NivelesEducativos).order_by(NivelesEducativos.id_nivel)).all()

    def obtener_asuntos(self):
        return db.session.scalars(db.select(Asuntos).order_by(Asuntos.descripcion)).all()

    def obtener_oficinas_por_municipio(self, id_municipio):
        return db.session.scalars(
            db.select(OficinasRegionales)
            .where(OficinasRegionales.id_municipio == id_municipio)
            .order_by(OficinasRegionales.oficina)
        ).all()

    # --- LÓGICA PRINCIPAL DEL TICKET (ACTUALIZADA Y CORREGIDA) ---
    def crear_turno(self, form_data):
        """
        Proceso transaccional para crear un solicitante y asignarle un turno,
        buscando el próximo horario disponible.
        """

        try:
            id_oficina = int(form_data.get('oficina'))
        except (ValueError, TypeError):
            print("❌ Error al crear turno: ID de oficina inválido o nulo.")
            return "ID de oficina inválido o nulo."

        # 1. NO LLAMAR A _encontrar_proximo_horario() AQUÍ FUERA

        try:
            # 2. Iniciar la transacción PRIMERO
            with db.session.begin():

                # 3. Buscar el horario DENTRO de la transacción
                (fecha_cita, hora_cita) = self._encontrar_proximo_horario(id_oficina)

                # 4. Si no hay slot, lanzar un error para forzar el ROLLBACK
                if fecha_cita is None:
                    raise ValueError(
                        "No se encontraron horarios disponibles. Asegúrese de que la oficina tenga horarios configurados en el admin.")

                # --- El resto de la lógica original ---
                curp_form = form_data.get('curp')

                solicitante = db.session.scalar(
                    db.select(Solicitantes).where(Solicitantes.curp == curp_form)
                )

                if not solicitante:
                    solicitante = Solicitantes(
                        nombre_tramitante=form_data.get('nombreCompleto'),
                        nombre_solicitante=form_data.get('nombre'),
                        paterno_solicitante=form_data.get('paterno'),
                        materno_solicitante=form_data.get('materno'),
                        curp=curp_form,
                        telefono=form_data.get('telefono'),
                        celular=form_data.get('celular'),
                        correo=form_data.get('correo')
                    )
                    db.session.add(solicitante)
                else:
                    solicitante.nombre_tramitante = form_data.get('nombreCompleto')
                    solicitante.nombre_solicitante = form_data.get('nombre')
                    solicitante.paterno_solicitante = form_data.get('paterno')
                    solicitante.materno_solicitante = form_data.get('materno')
                    solicitante.telefono = form_data.get('telefono')
                    solicitante.celular = form_data.get('celular')
                    solicitante.correo = form_data.get('correo')

                oficina_obj = db.session.get(OficinasRegionales, id_oficina)
                if not oficina_obj:
                    raise ValueError(f"ID de oficina no válido: {id_oficina}")

                id_municipio = oficina_obj.id_municipio

                contador = db.session.scalars(
                    db.select(ContadorTurnos)
                    .where(ContadorTurnos.id_municipio == id_municipio)
                    .with_for_update()
                ).one_or_none()

                if contador is None:
                    contador = ContadorTurnos(
                        id_municipio=id_municipio,
                        ultimo_turno=0
                    )
                    db.session.add(contador)

                contador.ultimo_turno += 1
                siguiente_turno_folio = contador.ultimo_turno

                nuevo_turno = Turnos(
                    numero_turno=siguiente_turno_folio,
                    codigo_qr=curp_form,
                    estado='pendiente',
                    fecha_solicitud=datetime.combine(fecha_cita, hora_cita),
                    hora_solicitud=hora_cita
                )

                nuevo_turno.solicitante = solicitante
                nuevo_turno.oficina = oficina_obj
                nuevo_turno.nivel = db.session.get(NivelesEducativos, form_data.get('nivel'))
                nuevo_turno.asunto = db.session.get(Asuntos, form_data.get('asunto'))

                db.session.add(nuevo_turno)

            # Si todo sale bien (el 'with' termina), el commit es automático
            return nuevo_turno

        except (SQLAlchemyError, ValueError) as e:
            # El "with" block ya hizo rollback automáticamente si hubo un error (SQLAlchemyError o el ValueError que lanzamos)
            error_msg = f"❌ Error al crear turno: {str(e)}"
            print(error_msg)
            return error_msg  # Devolver el STRING del error original

    def buscar_turno(self, numero_turno, curp):
        """ Busca un turno usando relaciones ORM. """
        return db.session.scalar(
            db.select(Turnos)
            .join(Turnos.solicitante)
            .where(
                Turnos.numero_turno == numero_turno,
                Solicitantes.curp == curp
            )
            .options(
                joinedload(Turnos.solicitante),
                joinedload(Turnos.oficina),
                joinedload(Turnos.nivel),
                joinedload(Turnos.asunto)
            )
        )

    def get_datos_comprobante(self, id_turno, curp):
        """ Obtiene todos los datos para el PDF y los devuelve como un DICT. """
        turno = db.session.scalar(
            db.select(Turnos)
            .options(
                joinedload(Turnos.solicitante),
                joinedload(Turnos.oficina).joinedload(OficinasRegionales.municipio),
                joinedload(Turnos.nivel),
                joinedload(Turnos.asunto)
            )
            .join(Turnos.solicitante)
            .where(
                Turnos.id_turno == id_turno,
                Solicitantes.curp == curp
            )
        )

        if not turno:
            return None

        return {
            'numero_turno': turno.numero_turno,
            'fecha_solicitud': turno.fecha_solicitud,
            'hora_solicitud': turno.hora_solicitud,
            'nombre_tramitante': turno.solicitante.nombre_tramitante,
            'nombre_solicitante': turno.solicitante.nombre_solicitante,
            'paterno_solicitante': turno.solicitante.paterno_solicitante,
            'materno_solicitante': turno.solicitante.materno_solicitante,
            'curp': turno.solicitante.curp,
            'telefono': turno.solicitante.telefono,
            'celular': turno.solicitante.celular,
            'correo': turno.solicitante.correo,
            'nivel': turno.nivel.nivel,
            'descripcion': turno.asunto.descripcion,
            'municipio': turno.oficina.municipio.municipio,
            'oficina': turno.oficina.oficina
        }

    # --- INICIO DE FUNCIONES FALTANTES ---

    def _get_catalogos_edicion(self):
        """Helper para cargar los catálogos necesarios para los formularios de edición."""
        return {
            'municipios': self.obtener_municipios(),
            'niveles': self.obtener_niveles(),
            'asuntos': self.obtener_asuntos(),
            'oficinas': db.session.scalars(db.select(OficinasRegionales)).all()  # Cargar todas para el admin
        }

    def buscar_turno_para_editar(self, numero_turno, curp):
        """
        Busca un turno para el público (debe estar pendiente).
        Devuelve el ticket y los catálogos.
        """
        ticket = db.session.scalar(
            db.select(Turnos)
            .join(Turnos.solicitante)
            .where(
                Turnos.numero_turno == numero_turno,
                Solicitantes.curp == curp,
                Turnos.estado == 'pendiente'  # Solo se pueden editar pendientes
            )
            .options(joinedload(Turnos.solicitante), joinedload(Turnos.oficina))
        )

        if not ticket:
            return None

        # Empaquetamos los datos del ticket para el formulario
        ticket_data = {
            'id_turno': ticket.id_turno,
            'numero_turno': ticket.numero_turno,
            'id_solicitante': ticket.id_solicitante,
            'nombre_tramitante': ticket.solicitante.nombre_tramitante,
            'curp': ticket.solicitante.curp,
            'nombre_solicitante': ticket.solicitante.nombre_solicitante,
            'paterno_solicitante': ticket.solicitante.paterno_solicitante,
            'materno_solicitante': ticket.solicitante.materno_solicitante,
            'telefono': ticket.solicitante.telefono,
            'celular': ticket.solicitante.celular,
            'correo': ticket.solicitante.correo,
            'id_nivel': ticket.id_nivel,
            'id_municipio': ticket.oficina.id_municipio,
            'id_oficina': ticket.id_oficina,
            'id_asunto': ticket.id_asunto
        }

        return {
            'ticket': ticket_data,
            'catalogos': self._get_catalogos_edicion()
        }

    def buscar_turno_admin_para_editar(self, id_turno):
        """
        Busca un turno para el admin (puede estar en cualquier estado).
        Devuelve el ticket y los catálogos.
        """
        ticket = db.session.scalar(
            db.select(Turnos)
            .where(Turnos.id_turno == id_turno)
            .options(joinedload(Turnos.solicitante), joinedload(Turnos.oficina))
        )

        if not ticket:
            return None

        # Empaquetamos los datos del ticket para el formulario
        ticket_data = {
            'id_turno': ticket.id_turno,
            'numero_turno': ticket.numero_turno,
            'id_solicitante': ticket.id_solicitante,
            'nombre_tramitante': ticket.solicitante.nombre_tramitante,
            'curp': ticket.solicitante.curp,
            'nombre_solicitante': ticket.solicitante.nombre_solicitante,
            'paterno_solicitante': ticket.solicitante.paterno_solicitante,
            'materno_solicitante': ticket.solicitante.materno_solicitante,
            'telefono': ticket.solicitante.telefono,
            'celular': ticket.solicitante.celular,
            'correo': ticket.solicitante.correo,
            'id_nivel': ticket.id_nivel,
            'id_municipio': ticket.oficina.id_municipio,
            'id_oficina': ticket.id_oficina,
            'id_asunto': ticket.id_asunto
        }

        return {
            'ticket': ticket_data,
            'catalogos': self._get_catalogos_edicion()
        }

    def actualizar_turno(self, form_data):
        """
        Actualiza un solicitante y su turno desde un formulario de edición.
        """
        try:
            id_solicitante = form_data.get('id_solicitante', type=int)
            id_turno = form_data.get('id_turno', type=int)

            with db.session.begin():
                # 1. Obtener los objetos
                solicitante = db.session.get(Solicitantes, id_solicitante)
                turno = db.session.get(Turnos, id_turno)

                if not solicitante or not turno:
                    print("Error: No se encontró solicitante o turno.")
                    return False

                # 2. Actualizar datos del Solicitante
                solicitante.nombre_tramitante = form_data.get('nombreCompleto')
                solicitante.nombre_solicitante = form_data.get('nombre')
                solicitante.paterno_solicitante = form_data.get('paterno')
                solicitante.materno_solicitante = form_data.get('materno')
                solicitante.curp = form_data.get('curp')
                solicitante.telefono = form_data.get('telefono')
                solicitante.celular = form_data.get('celular')
                solicitante.correo = form_data.get('correo')

                # 3. Actualizar datos del Turno
                turno.id_nivel = form_data.get('nivel', type=int)
                turno.id_oficina = form_data.get('oficina', type=int)
                turno.id_asunto = form_data.get('asunto', type=int)

                # (Nota: No actualizamos la fecha/hora/folio, solo los datos del trámite)

            # Si el 'with' termina sin error, el commit es automático
            return True
        except (SQLAlchemyError, ValueError) as e:
            db.session.rollback()
            print(f"Error al actualizar turno: {e}")
            return False

    # --- FIN DE FUNCIONES FALTANTES ---

    def buscar_turnos_admin(self, query, vista="activos"):
        """ Busca turnos usando ORM con JOINs y filtro ILIKE. """
        try:
            search_query = f"%{query}%"
            stmt = db.select(Turnos).options(
                joinedload(Turnos.solicitante),
                joinedload(Turnos.oficina)
            ).join(Turnos.solicitante)

            if query:
                stmt = stmt.where(
                    or_(
                        Solicitantes.curp.ilike(search_query),
                        Solicitantes.nombre_solicitante.ilike(search_query)
                    )
                )

            if vista == "cancelados":
                stmt = stmt.where(Turnos.estado == 'cancelado')
            else:
                stmt = stmt.where(Turnos.estado != 'cancelado')

            stmt = stmt.order_by(Turnos.fecha_solicitud.desc()).limit(50)
            return db.session.scalars(stmt).all()
        except SQLAlchemyError as e:
            print(f"Error al buscar turnos (admin): {e}")
            return []

    def cambiar_estado_turno(self, id_turno, nuevo_estado):
        """ Actualiza el estado de un turno. """
        if nuevo_estado not in ('pendiente', 'resuelto'):
            return False
        try:
            turno = db.session.get(Turnos, id_turno)
            if turno:
                turno.estado = nuevo_estado
                db.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Error al cambiar estado: {e}")
            return False

    def eliminar_turno_admin(self, id_turno):
        """ 'Elimina' un turno (soft delete). """
        return self.cambiar_estado_turno(id_turno, 'cancelado')

    def get_stats_dashboard(self):
        """ Obtiene las estadísticas para el dashboard usando ORM. """
        try:
            totales_query = db.select(Turnos.estado, func.count(Turnos.id_turno)) \
                .group_by(Turnos.estado)
            totales_data_raw = db.session.execute(totales_query).all()
            totales_data = [{'estado': r[0], 'total': r[1]} for r in totales_data_raw]

            municipios_query = db.select(Municipios.municipio, Turnos.estado, func.count(Turnos.id_turno)) \
                .join(Turnos.oficina) \
                .join(OficinasRegionales.municipio) \
                .where(Turnos.estado.in_(['pendiente', 'resuelto', 'cancelado'])) \
                .group_by(Municipios.municipio, Turnos.estado) \
                .order_by(Municipios.municipio, Turnos.estado)
            municipios_data_raw = db.session.execute(municipios_query).all()

            municipios_proc = {}
            for row in municipios_data_raw:
                muni, estado, total = row
                if muni not in municipios_proc:
                    municipios_proc[muni] = {'pendiente': 0, 'resuelto': 0, 'cancelado': 0}
                if estado in municipios_proc[muni]:
                    municipios_proc[muni][estado] = total

            return {
                "totales": totales_data,
                "por_municipio": municipios_proc
            }
        except SQLAlchemyError as e:
            print(f"Error al obtener estadísticas del dashboard: {e}")
            return None

    def eliminar_turno_publico(self, numero_turno, curp):
        """
        Busca un turno por su número y CURP del solicitante,
        y lo marca como 'cancelado' si está 'pendiente'.
        Retorna True si fue exitoso, False en caso contrario.
        """
        try:
            turno_a_cancelar = db.session.scalar(
                db.select(Turnos)
                .join(Turnos.solicitante)
                .where(
                    Turnos.numero_turno == numero_turno,
                    Solicitantes.curp == curp,
                    Turnos.estado == 'pendiente'
                )
            )

            if not turno_a_cancelar:
                return False

            turno_a_cancelar.estado = 'cancelado'
            db.session.commit()
            return True

        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Error al intentar cancelar turno público: {e}")
            return False