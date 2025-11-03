# controllers/ticket_controller.py
from DB.db import Database
from models.solicitante import Solicitante
from models.turno import Turno
import pymysql


class TicketController:

    def __init__(self):
        self.db = Database()

    # --- MÉTODOS PARA OBTENER CATÁLOGOS ---
    def obtener_municipios(self):
        return self.db.fetchall("SELECT id_municipio, municipio FROM municipios ORDER BY municipio")

    def obtener_niveles(self):
        return self.db.fetchall("SELECT id_nivel, nivel FROM niveles_educativos ORDER BY id_nivel")

    def obtener_asuntos(self):
        return self.db.fetchall("SELECT id_asunto, descripcion FROM asuntos ORDER BY descripcion")

    def obtener_oficinas_por_municipio(self, id_municipio):
        # Tu API original, ahora usada para poblar el select de oficinas
        return self.db.fetchall(
            "SELECT id_oficina, oficina FROM oficinas_regionales WHERE id_municipio = %s ORDER BY oficina",
            (id_municipio,)
        )

    # --- LÓGICA PRINCIPAL DEL TICKET ---
    def crear_turno(self, form_data):
        """
        Proceso transaccional para crear un solicitante y asignarle un turno.
        """
        conn = None
        try:
            conn = self.db.conectar()
            with conn.cursor() as cur:

                # 1. Gestionar Solicitante (Crear o recuperar ID)
                solicitante = Solicitante.from_form(form_data)
                cur.execute("SELECT id_solicitante FROM solicitantes WHERE curp = %s", (solicitante.curp,))
                resultado = cur.fetchone()

                if resultado:
                    id_solicitante = resultado['id_solicitante']
                else:
                    sql_solicitante = """
                                      INSERT INTO solicitantes (nombre_tramitante, nombre_solicitante, \
                                                                paterno_solicitante,
                                                                materno_solicitante, curp, telefono, celular, correo)
                                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s) \
                                      """
                    params_solicitante = (solicitante.nombre_tramitante, solicitante.nombre_solicitante,
                                          solicitante.paterno_solicitante, solicitante.materno_solicitante,
                                          solicitante.curp, solicitante.telefono, solicitante.celular,
                                          solicitante.correo)
                    cur.execute(sql_solicitante, params_solicitante)
                    id_solicitante = cur.lastrowid

                # 2. Obtener el siguiente turno para el municipio
                id_oficina = form_data.get('oficina')

                # --- INICIO DE LA VALIDACIÓN (ARREGLO) ---
                cur.execute("SELECT id_municipio FROM oficinas_regionales WHERE id_oficina = %s", (id_oficina,))
                oficina_data = cur.fetchone()  # Primero guardamos en una variable

                if not oficina_data:
                    # Si no se encontró la oficina (el ID es inválido o vacío)
                    conn.rollback()  # Cancelamos la transacción
                    print(f"❌ Error: ID de oficina no válido o no seleccionado: '{id_oficina}'")
                    return None  # Salimos de la función

                # Ahora es seguro acceder al dato
                id_municipio = oficina_data['id_municipio']
                # --- FIN DE LA VALIDACIÓN (ARREGLO) ---

                # Bloqueamos la fila del municipio para evitar concurrencia
                cur.execute("SELECT ultimo_turno FROM contador_turnos WHERE id_municipio = %s FOR UPDATE",
                            (id_municipio,))
                contador = cur.fetchone()

                siguiente_turno = contador['ultimo_turno'] + 1

                # Actualizamos el contador
                cur.execute("UPDATE contador_turnos SET ultimo_turno = %s WHERE id_municipio = %s",
                            (siguiente_turno, id_municipio))

                # 3. Crear el Turno
                nuevo_turno = Turno.from_form(form_data)
                nuevo_turno.id_solicitante = id_solicitante
                nuevo_turno.numero_turno = siguiente_turno
                nuevo_turno.codigo_qr = solicitante.curp

                sql_turno = """
                            INSERT INTO turnos (id_solicitante, id_oficina, numero_turno, id_nivel, id_asunto, estado, \
                                                codigo_qr, fecha_solicitud)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) \
                            """
                params_turno = (nuevo_turno.id_solicitante, nuevo_turno.id_oficina, nuevo_turno.numero_turno,
                                nuevo_turno.id_nivel, nuevo_turno.id_asunto, nuevo_turno.estado,
                                nuevo_turno.codigo_qr, nuevo_turno.fecha_solicitud)
                cur.execute(sql_turno, params_turno)
                nuevo_turno.id_turno = cur.lastrowid

                conn.commit()

                nuevo_turno.solicitante = solicitante
                return nuevo_turno

        except pymysql.MySQLError as e:
            if conn:
                conn.rollback()
            print(f"❌ Error al crear turno: {e}")
            return None
        finally:
            if conn:
                self.db.desconectar()

    def buscar_turno(self, numero_turno, curp):
        """
        Busca un turno uniendo las tablas turnos y solicitantes.
        """
        sql = """
              SELECT t.*, s.nombre_tramitante, s.curp, o.oficina
              FROM turnos t
                       JOIN solicitantes s ON t.id_solicitante = s.id_solicitante
                       JOIN oficinas_regionales o ON t.id_oficina = o.id_oficina
              WHERE t.numero_turno = %s \
                AND s.curp = %s \
              """
        return self.db.fetchone(sql, (numero_turno, curp))

    def buscar_turno_para_editar(self, turno, curp):
        """
        Busca un turno y trae todos los datos necesarios para
        poblar el formulario de edición.
        """
        try:
            conn = self.db.conectar()
            with conn.cursor() as cur:
                # 1. Buscar el turno y solicitante
                sql = """
                      SELECT t.*, s.*, o.id_municipio
                      FROM turnos t
                               JOIN solicitantes s ON t.id_solicitante = s.id_solicitante
                               JOIN oficinas_regionales o ON t.id_oficina = o.id_oficina
                      WHERE t.numero_turno = %s \
                        AND s.curp = %s \
                        AND t.estado = 'pendiente' \
                      """
                cur.execute(sql, (turno, curp))
                ticket_data = cur.fetchone()

                if not ticket_data:
                    return None  # No se encontró o ya no está pendiente

                # 2. Obtener todos los catálogos para los <select>
                cur.execute("SELECT id_municipio, municipio FROM municipios ORDER BY municipio")
                municipios = cur.fetchall()

                cur.execute(
                    "SELECT id_oficina, oficina FROM oficinas_regionales WHERE id_municipio = %s ORDER BY oficina",
                    (ticket_data['id_municipio'],))
                oficinas = cur.fetchall()

                cur.execute("SELECT id_nivel, nivel FROM niveles_educativos ORDER BY id_nivel")
                niveles = cur.fetchall()

                cur.execute("SELECT id_asunto, descripcion FROM asuntos ORDER BY descripcion")
                asuntos = cur.fetchall()

                return {
                    "ticket": ticket_data,
                    "catalogos": {
                        "municipios": municipios,
                        "oficinas": oficinas,
                        "niveles": niveles,
                        "asuntos": asuntos
                    }
                }
        except Exception as e:
            print(f"Error al buscar turno para editar: {e}")
            return None
        finally:
            self.db.desconectar()

    def buscar_turno_admin_para_editar(self, id_turno):
        """
        Busca un turno por su ID para el panel de admin.
        No requiere CURP ni estado 'pendiente'.
        """
        try:
            conn = self.db.conectar()
            with conn.cursor() as cur:
                # 1. Buscar el turno y solicitante por id_turno
                sql = """
                      SELECT t.*, s.*, o.id_municipio
                      FROM turnos t
                               JOIN solicitantes s ON t.id_solicitante = s.id_solicitante
                               JOIN oficinas_regionales o ON t.id_oficina = o.id_oficina
                      WHERE t.id_turno = %s
                      """
                cur.execute(sql, (id_turno,))
                ticket_data = cur.fetchone()

                if not ticket_data:
                    return None  # No se encontró

                # 2. Obtener todos los catálogos para los <select>
                cur.execute("SELECT id_municipio, municipio FROM municipios ORDER BY municipio")
                municipios = cur.fetchall()

                cur.execute(
                    "SELECT id_oficina, oficina FROM oficinas_regionales WHERE id_municipio = %s ORDER BY oficina",
                    (ticket_data['id_municipio'],))
                oficinas = cur.fetchall()

                cur.execute("SELECT id_nivel, nivel FROM niveles_educativos ORDER BY id_nivel")
                niveles = cur.fetchall()

                cur.execute("SELECT id_asunto, descripcion FROM asuntos ORDER BY descripcion")
                asuntos = cur.fetchall()

                return {
                    "ticket": ticket_data,
                    "catalogos": {
                        "municipios": municipios,
                        "oficinas": oficinas,
                        "niveles": niveles,
                        "asuntos": asuntos
                    }
                }
        except Exception as e:
            print(f"Error al buscar turno admin para editar: {e}")
            return None
        finally:
            self.db.desconectar()

    def actualizar_turno(self, form_data):
        """
        Actualiza un solicitante y su turno en la base de datos.
        """
        conn = None
        try:
            conn = self.db.conectar()
            with conn.cursor() as cur:

                id_solicitante = form_data.get('id_solicitante')
                id_turno = form_data.get('id_turno')

                # 1. Actualizar tabla 'solicitantes'
                sql_sol = """
                          UPDATE solicitantes \
                          SET nombre_tramitante   = %s, \
                              nombre_solicitante  = %s, \
                              paterno_solicitante = %s, \
                              materno_solicitante = %s, \
                              curp                = %s, \
                              telefono            = %s, \
                              celular             = %s, \
                              correo              = %s
                          WHERE id_solicitante = %s \
                          """
                cur.execute(sql_sol, (
                    form_data.get('nombreCompleto'), form_data.get('nombre'), form_data.get('paterno'),
                    form_data.get('materno'), form_data.get('curp'), form_data.get('telefono'),
                    form_data.get('celular'), form_data.get('correo'), id_solicitante
                ))

                # 2. Actualizar tabla 'turnos'
                sql_turno = """
                            UPDATE turnos \
                            SET id_nivel   = %s, \
                                id_asunto  = %s, \
                                id_oficina = %s
                            WHERE id_turno = %s \
                            """
                cur.execute(sql_turno, (
                    form_data.get('nivel'), form_data.get('asunto'), form_data.get('oficina'), id_turno
                ))

                conn.commit()
                return True

        except pymysql.MySQLError as e:
            if conn:
                conn.rollback()
            print(f"Error al actualizar turno: {e}")
            return False
        finally:
            if conn:
                self.db.desconectar()

    def get_datos_comprobante(self, id_turno, curp):
        """
        Obtiene todos los datos (con JOINs) necesarios para generar el PDF
        y valida que el CURP coincida.
        """
        sql = """
              SELECT t.numero_turno, \
                     t.fecha_solicitud, \
                     s.nombre_tramitante, \
                     s.nombre_solicitante, \
                     s.paterno_solicitante, \
                     s.materno_solicitante, \
                     s.curp, \
                     s.telefono, \
                     s.celular, \
                     s.correo, \
                     n.nivel, \
                     a.descripcion, \
                     m.municipio, \
                     o.oficina
              FROM turnos t
                       JOIN solicitantes s ON t.id_solicitante = s.id_solicitante
                       JOIN niveles_educativos n ON t.id_nivel = n.id_nivel
                       JOIN asuntos a ON t.id_asunto = a.id_asunto
                       JOIN oficinas_regionales o ON t.id_oficina = o.id_oficina
                       JOIN municipios m ON o.id_municipio = m.id_municipio
              WHERE t.id_turno = %s \
                AND s.curp = %s \
              """
        try:
            return self.db.fetchone(sql, (id_turno, curp))
        except Exception as e:
            print(f"Error al obtener datos del comprobante: {e}")
            return None
        finally:
            self.db.desconectar()

    # --- INICIO DE LA MODIFICACIÓN ---
    def buscar_turnos_admin(self, query, vista="activos"):
        """
        Busca turnos por CURP o nombre del solicitante.
        Ahora filtra por 'vista' (activos o cancelados).
        """
        try:
            search_query = f"%{query}%"

            sql_base = """
                       SELECT t.id_turno, \
                              t.numero_turno, \
                              t.estado, \
                              t.fecha_solicitud, \
                              s.nombre_solicitante, \
                              s.curp, \
                              o.oficina
                       FROM turnos t
                                JOIN solicitantes s ON t.id_solicitante = s.id_solicitante
                                JOIN oficinas_regionales o ON t.id_oficina = o.id_oficina
                       WHERE (s.curp LIKE %s \
                           OR s.nombre_solicitante LIKE %s) \
                       """

            # Filtro de estado dinámico
            if vista == "cancelados":
                sql_filtro_estado = " AND t.estado = 'cancelado'"
            else:
                # La vista por defecto (activos) oculta los cancelados
                sql_filtro_estado = " AND t.estado != 'cancelado'"

            sql_orden = " ORDER BY t.fecha_solicitud DESC LIMIT 50;"

            sql_final = sql_base + sql_filtro_estado + sql_orden

            return self.db.fetchall(sql_final, (search_query, search_query))

        except Exception as e:
            print(f"Error al buscar turnos (admin): {e}")
            return []

    # --- FIN DE LA MODIFICACIÓN ---

    def cambiar_estado_turno(self, id_turno, nuevo_estado):
        """
        Actualiza el estado de un turno a 'pendiente' o 'resuelto'.
        Req. 5: "colocar un estatus de 'Resuelto' y 'Pendiente'"
        """
        if nuevo_estado not in ('pendiente', 'resuelto'):
            print(f"Error: Estado '{nuevo_estado}' no válido.")
            return False

        try:
            sql = "UPDATE turnos SET estado = %s WHERE id_turno = %s"
            # execute maneja la conexión y el commit
            self.db.execute(sql, (nuevo_estado, id_turno), commit=True)
            return True
        except Exception as e:
            print(f"Error al cambiar estado: {e}")
            return False

    def eliminar_turno_admin(self, id_turno):
        """
        Elimina un turno (Req. 5).
        Usamos un 'soft delete' cambiando el estado a 'cancelado'
        para mantener la integridad de los datos.
        """
        try:
            sql = "UPDATE turnos SET estado = 'cancelado' WHERE id_turno = %s"
            self.db.execute(sql, (id_turno,), commit=True)
            return True
        except Exception as e:
            print(f"Error al eliminar/cancelar turno: {e}")
            return False