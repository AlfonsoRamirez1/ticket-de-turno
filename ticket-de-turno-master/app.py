# app.py
import time
from datetime import datetime
from flask import (Flask, render_template, request, jsonify, abort,
                   session, redirect, url_for, flash, Response)
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
import random

# --- INICIO DE CONFIGURACIÓN ORM ---
from config import Config
from db import db  # Importamos la instancia de la BD
from flask_bcrypt import Bcrypt
# --- FIN DE CONFIGURACIÓN ORM ---

# --- Importamos los controladores REFACTORIZADOS ---
from controllers.ticket_controller import TicketController
from controllers.auth_controller import AuthController
from controllers.catalogo_controller import CatalogoController
from utils.pdf_rl import crear_comprobante_rl

app = Flask(__name__)
app.config.from_object(Config)

# --- Inicializar extensiones ---
db.init_app(app)
bcrypt = Bcrypt(app)  # bcrypt lo usa app.py para el login_post

# --- CONFIGURACIÓN DE FLASK-LOGIN ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_get'
login_manager.login_message = 'Por favor, inicie sesión para acceder a esta página.'
login_manager.login_message_category = 'error'

# --- Instanciamos controladores ---
ticket_controller = TicketController()
auth_controller = AuthController()
catalogo_controller = CatalogoController()


@login_manager.user_loader
def load_user(user_id):
    # Ahora usamos el controlador refactorizado
    return auth_controller.get_user_by_id(user_id)


# --- CACHE BUSTER ---
@app.context_processor
def utility_processor():
    return dict(cache_buster=int(time.time()))


# --- RUTAS DE AUTENTICACIÓN ---
@app.get("/login")
def login_get():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    num1 = random.randint(1, 9)
    num2 = random.randint(1, 9)
    session['captcha_answer'] = num1 + num2
    return render_template("login.html", num1=num1, num2=num2)


@app.post("/login")
def login_post():
    usuario = request.form.get('usuario')
    password_ingresada = request.form.get('password')
    captcha_input = request.form.get('captcha')

    try:
        if 'captcha_answer' not in session or int(captcha_input) != session['captcha_answer']:
            flash('Respuesta incorrecta del Captcha.', 'error')
            return redirect(url_for('login_get'))
    except (ValueError, TypeError):
        flash('Respuesta de Captcha inválida.', 'error')
        return redirect(url_for('login_get'))

    # Usamos el controlador refactorizado
    admin = auth_controller.validar_login(usuario, password_ingresada)

    if admin:
        login_user(admin)
        session.pop('captcha_answer', None)
        return redirect(url_for('admin_dashboard'))
    else:
        flash('Usuario o contraseña incorrectos.', 'error')
        return redirect(url_for('login_get'))


@app.get("/admin/dashboard")
@login_required
def admin_dashboard():
    return render_template("admin_dashboard.html")


@app.get("/logout")
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión exitosamente.', 'success')
    return redirect(url_for('login_get'))


# ---------------------------
# RUTAS DE ADMINISTRACIÓN (TURNOS)
# ---------------------------

@app.get("/admin/turnos")
@login_required
def admin_turnos_get():
    query = request.args.get("q", "")
    vista = request.args.get("vista", "activos")
    turnos = ticket_controller.buscar_turnos_admin(query, vista)
    return render_template("admin_turnos.html",
                           turnos=turnos,
                           query=query,
                           vista=vista)


@app.post("/admin/turnos/cambiar_estado")
@login_required
def admin_cambiar_estado():
    id_turno = request.form.get("id_turno")
    nuevo_estado = request.form.get("nuevo_estado")

    if not id_turno or nuevo_estado not in ('pendiente', 'resuelto'):
        flash("Datos incorrectos para cambiar estado.", "error")
        return redirect(url_for('admin_turnos_get'))

    exito = ticket_controller.cambiar_estado_turno(id_turno, nuevo_estado)
    if exito:
        flash(f"Turno #{id_turno} actualizado a '{nuevo_estado}'.", "success")
    else:
        flash("Error al actualizar el estado.", "error")

    vista = request.args.get("vista", "activos")
    return redirect(url_for('admin_turnos_get', vista=vista))


@app.post("/admin/turnos/eliminar")
@login_required
def admin_eliminar_turno():
    id_turno = request.form.get("id_turno")
    exito = ticket_controller.eliminar_turno_admin(id_turno)
    if exito:
        flash(f"Turno #{id_turno} marcado como 'cancelado'.", "success")
    else:
        flash("Error al cancelar el turno.", "error")

    vista = request.args.get("vista", "activos")
    return redirect(url_for('admin_turnos_get', vista=vista))


@app.get("/admin/turnos/crear")
@login_required
def admin_crear_get():
    municipios = ticket_controller.obtener_municipios()
    niveles = ticket_controller.obtener_niveles()
    asuntos = ticket_controller.obtener_asuntos()
    return render_template("admin_crear_turno.html",
                           municipios=municipios,
                           niveles=niveles,
                           asuntos=asuntos)


@app.post("/admin/turnos/crear")
@login_required
def admin_crear_post():
    datos_formulario = request.form
    nuevo_turno = ticket_controller.crear_turno(datos_formulario)
    if nuevo_turno:
        flash(f"Turno #{nuevo_turno.numero_turno} creado exitosamente para {nuevo_turno.solicitante.curp}.", "success")
        return redirect(url_for('admin_turnos_get'))
    else:
        flash("Error al crear el turno. Verifique los datos.", "error")
        return redirect(url_for('admin_crear_get'))


@app.get("/admin/turnos/editar/<int:id_turno>")
@login_required
def admin_editar_get(id_turno):
    data = ticket_controller.buscar_turno_admin_para_editar(id_turno)

    if data:
        return render_template("admin_editar_turno.html",
                               ticket=data['ticket'],
                               catalogos=data['catalogos'],
                               vista=request.args.get("vista", "activos"))
    else:
        flash("Ticket no encontrado.", 'error')
        return redirect(url_for('admin_turnos_get'))


@app.post("/admin/turnos/editar")
@login_required
def admin_editar_post():
    exito = ticket_controller.actualizar_turno(request.form)
    if exito:
        flash("¡Ticket actualizado con éxito!", 'success')
    else:
        flash("Error al actualizar el ticket. Intente de nuevo.", 'error')

    vista = request.form.get("vista", "activos")
    return redirect(url_for('admin_turnos_get', vista=vista))


# ---------------------------
# RUTA API PARA DASHBOARD
# ---------------------------
@app.get("/admin/dashboard/stats")
@login_required
def admin_dashboard_stats():
    """ API endpoint para los datos del dashboard. """
    datos = ticket_controller.get_stats_dashboard()
    if datos:
        return jsonify(datos)
    else:
        return jsonify({"error": "No se pudieron cargar las estadísticas"}), 500


# ---------------------------
# RUTAS CRUD CATÁLOGOS
# ---------------------------

@app.get("/admin/catalogos")
@login_required
def admin_catalogos_menu():
    return render_template("admin_catalogos_menu.html")


# --- RUTAS PARA MUNICIPIOS ---
@app.get("/admin/catalogos/municipios")
@login_required
def admin_municipios_get():
    municipios = catalogo_controller.get_municipios()
    return render_template("admin_cat_municipios.html", municipios=municipios)


@app.post("/admin/catalogos/municipios/crear")
@login_required
def admin_municipios_crear():
    nombre = request.form.get("nombre")
    exito, mensaje = catalogo_controller.crear_municipio(nombre)
    flash(mensaje, "success" if exito else "error")
    return redirect(url_for('admin_municipios_get'))


@app.get("/admin/catalogos/municipios/editar/<int:id_municipio>")
@login_required
def admin_municipios_editar_get(id_municipio):
    municipio = catalogo_controller.get_municipio_by_id(id_municipio)
    if not municipio:
        flash("Municipio no encontrado.", "error")
        return redirect(url_for('admin_municipios_get'))
    return render_template("admin_cat_municipio_editar.html", municipio=municipio)


@app.post("/admin/catalogos/municipios/editar")
@login_required
def admin_municipios_editar_post():
    id_municipio = request.form.get("id_municipio")
    nombre = request.form.get("nombre")
    exito, mensaje = catalogo_controller.actualizar_municipio(id_municipio, nombre)
    flash(mensaje, "success" if exito else "error")
    return redirect(url_for('admin_municipios_get'))


@app.post("/admin/catalogos/municipios/eliminar")
@login_required
def admin_municipios_eliminar():
    id_municipio = request.form.get("id_municipio")
    exito, mensaje = catalogo_controller.eliminar_municipio(id_municipio)
    flash(mensaje, "success" if exito else "error")
    return redirect(url_for('admin_municipios_get'))


# --- RUTAS PARA NIVELES EDUCATIVOS ---
@app.get("/admin/catalogos/niveles")
@login_required
def admin_niveles_get():
    niveles = catalogo_controller.get_niveles()
    return render_template("admin_cat_niveles.html", niveles=niveles)


@app.post("/admin/catalogos/niveles/crear")
@login_required
def admin_niveles_crear():
    nombre = request.form.get("nombre")
    exito, mensaje = catalogo_controller.crear_nivel(nombre)
    flash(mensaje, "success" if exito else "error")
    return redirect(url_for('admin_niveles_get'))


@app.get("/admin/catalogos/niveles/editar/<int:id_nivel>")
@login_required
def admin_niveles_editar_get(id_nivel):
    nivel = catalogo_controller.get_nivel_by_id(id_nivel)
    if not nivel:
        flash("Nivel no encontrado.", "error")
        return redirect(url_for('admin_niveles_get'))
    return render_template("admin_cat_nivel_editar.html", nivel=nivel)


@app.post("/admin/catalogos/niveles/editar")
@login_required
def admin_niveles_editar_post():
    id_nivel = request.form.get("id_nivel")
    nombre = request.form.get("nombre")
    exito, mensaje = catalogo_controller.actualizar_nivel(id_nivel, nombre)
    flash(mensaje, "success" if exito else "error")
    return redirect(url_for('admin_niveles_get'))


@app.post("/admin/catalogos/niveles/eliminar")
@login_required
def admin_niveles_eliminar():
    id_nivel = request.form.get("id_nivel")
    exito, mensaje = catalogo_controller.eliminar_nivel(id_nivel)
    flash(mensaje, "success" if exito else "error")
    return redirect(url_for('admin_niveles_get'))


# --- RUTAS PARA ASUNTOS ---
@app.get("/admin/catalogos/asuntos")
@login_required
def admin_asuntos_get():
    asuntos = catalogo_controller.get_asuntos()
    return render_template("admin_cat_asuntos.html", asuntos=asuntos)


@app.post("/admin/catalogos/asuntos/crear")
@login_required
def admin_asuntos_crear():
    descripcion = request.form.get("descripcion")
    exito, mensaje = catalogo_controller.crear_asunto(descripcion)
    flash(mensaje, "success" if exito else "error")
    return redirect(url_for('admin_asuntos_get'))


@app.get("/admin/catalogos/asuntos/editar/<int:id_asunto>")
@login_required
def admin_asuntos_editar_get(id_asunto):
    asunto = catalogo_controller.get_asunto_by_id(id_asunto)
    if not asunto:
        flash("Asunto no encontrado.", "error")
        return redirect(url_for('admin_asuntos_get'))
    return render_template("admin_cat_asunto_editar.html", asunto=asunto)


@app.post("/admin/catalogos/asuntos/editar")
@login_required
def admin_asuntos_editar_post():
    id_asunto = request.form.get("id_asunto")
    descripcion = request.form.get("descripcion")
    exito, mensaje = catalogo_controller.actualizar_asunto(id_asunto, descripcion)
    flash(mensaje, "success" if exito else "error")
    return redirect(url_for('admin_asuntos_get'))


@app.post("/admin/catalogos/asuntos/eliminar")
@login_required
def admin_asuntos_eliminar():
    id_asunto = request.form.get("id_asunto")
    exito, mensaje = catalogo_controller.eliminar_asunto(id_asunto)
    flash(mensaje, "success" if exito else "error")
    return redirect(url_for('admin_asuntos_get'))


# --- RUTAS PARA OFICINAS REGIONALES ---
@app.get("/admin/catalogos/oficinas")
@login_required
def admin_oficinas_get():
    oficinas = catalogo_controller.get_oficinas()
    municipios = catalogo_controller.get_municipios()
    return render_template("admin_cat_oficinas.html", oficinas=oficinas, municipios=municipios)


@app.post("/admin/catalogos/oficinas/crear")
@login_required
def admin_oficinas_crear():
    nombre = request.form.get("nombre")
    id_municipio = request.form.get("id_municipio")
    exito, mensaje = catalogo_controller.crear_oficina(nombre, id_municipio)
    flash(mensaje, "success" if exito else "error")
    return redirect(url_for('admin_oficinas_get'))


@app.get("/admin/catalogos/oficinas/editar/<int:id_oficina>")
@login_required
def admin_oficinas_editar_get(id_oficina):
    oficina = catalogo_controller.get_oficina_by_id(id_oficina)
    if not oficina:
        flash("Oficina no encontrada.", "error")
        return redirect(url_for('admin_oficinas_get'))
    municipios = catalogo_controller.get_municipios()
    return render_template("admin_cat_oficina_editar.html", oficina=oficina, municipios=municipios)


@app.post("/admin/catalogos/oficinas/editar")
@login_required
def admin_oficinas_editar_post():
    id_oficina = request.form.get("id_oficina")
    nombre = request.form.get("nombre")
    id_municipio = request.form.get("id_municipio")
    exito, mensaje = catalogo_controller.actualizar_oficina(id_oficina, nombre, id_municipio)
    flash(mensaje, "success" if exito else "error")
    return redirect(url_for('admin_oficinas_get'))


@app.post("/admin/catalogos/oficinas/eliminar")
@login_required
def admin_oficinas_eliminar():
    id_oficina = request.form.get("id_oficina")
    exito, mensaje = catalogo_controller.eliminar_oficina(id_oficina)
    flash(mensaje, "success" if exito else "error")
    return redirect(url_for('admin_oficinas_get'))


# --- RUTAS PARA HORARIOS (NUEVO) ---
@app.get("/admin/catalogos/horarios")
@login_required
def admin_horarios_get():
    horarios = catalogo_controller.get_horarios()
    # También pasamos las oficinas para el dropdown del formulario de creación
    oficinas = catalogo_controller.get_oficinas()
    return render_template("admin_cat_horarios.html", horarios=horarios, oficinas=oficinas)


@app.post("/admin/catalogos/horarios/crear")
@login_required
def admin_horarios_crear():
    exito, mensaje = catalogo_controller.crear_horario(request.form)
    flash(mensaje, "success" if exito else "error")
    return redirect(url_for('admin_horarios_get'))


@app.get("/admin/catalogos/horarios/editar/<int:id_horario>")
@login_required
def admin_horarios_editar_get(id_horario):
    horario = catalogo_controller.get_horario_by_id(id_horario)
    if not horario:
        flash("Horario no encontrado.", "error")
        return redirect(url_for('admin_horarios_get'))
    # Pasamos las oficinas para el dropdown
    oficinas = catalogo_controller.get_oficinas()
    return render_template("admin_cat_horario_editar.html", horario=horario, oficinas=oficinas)


@app.post("/admin/catalogos/horarios/editar")
@login_required
def admin_horarios_editar_post():
    exito, mensaje = catalogo_controller.actualizar_horario(request.form)
    flash(mensaje, "success" if exito else "error")
    return redirect(url_for('admin_horarios_get'))


@app.post("/admin/catalogos/horarios/eliminar")
@login_required
def admin_horarios_eliminar():
    id_horario = request.form.get("id_horario")
    exito, mensaje = catalogo_controller.eliminar_horario(id_horario)
    flash(mensaje, "success" if exito else "error")
    return redirect(url_for('admin_horarios_get'))


# ---------------------------
# RUTAS PÚBLICAS (Tickets)
# ---------------------------
@app.get("/inicio")
def inicio():
    return render_template("inicio.html")


@app.get("/crear")
def crear_get():
    municipios = ticket_controller.obtener_municipios()
    niveles = ticket_controller.obtener_niveles()
    asuntos = ticket_controller.obtener_asuntos()
    return render_template("CrearTicket.html",
                           municipios=municipios,
                           niveles=niveles,
                           asuntos=asuntos)


@app.post("/crear")
def crear_post():
    datos_formulario = request.form
    nuevo_turno = ticket_controller.crear_turno(datos_formulario)
    if nuevo_turno:
        return render_template("ticket_generado.html",
                               turno=nuevo_turno,
                               solicitante=nuevo_turno.solicitante)
    else:
        flash("Error al crear el turno. Verifique sus datos o intente más tarde.", "error")
        return redirect(url_for('crear_get'))


@app.get("/ver")
def ver_get():
    turno_num = request.args.get("turno")
    curp = request.args.get("curp")
    ticket_encontrado = None
    mensaje_error = None
    if turno_num and curp:
        ticket_encontrado = ticket_controller.buscar_turno(turno_num, curp)
        if not ticket_encontrado:
            mensaje_error = "No se encontró ningún ticket con esa CURP y número de turno."
    return render_template("verTicket.html",
                           ticket=ticket_encontrado,
                           error=mensaje_error)


@app.get("/actualizar")
def actualizar_get():
    return render_template("actualizarTicket.html")


@app.get("/actualizar/editar")
def actualizar_buscar():
    curp = request.args.get("curp")
    turno = request.args.get("turno")
    data = ticket_controller.buscar_turno_para_editar(turno, curp)
    if data:
        return render_template("editarTicket.html",
                               ticket=data['ticket'],
                               catalogos=data['catalogos'])
    else:
        flash("Ticket no encontrado, no está 'Pendiente' o los datos son incorrectos.", 'error')
        return redirect(url_for('actualizar_get'))


@app.post("/actualizar/editar")
def actualizar_guardar():
    exito = ticket_controller.actualizar_turno(request.form)
    if exito:
        flash("¡Ticket actualizado con éxito!", 'success')
        return redirect(url_for('actualizar_get'))
    else:
        flash("Error al actualizar el ticket. Intente de nuevo.", 'error')
        return redirect(url_for('actualizar_get'))


@app.get("/eliminar")
def eliminar_get():
    return render_template("eliminarTicket.html")


@app.post("/eliminar")
def eliminar_post():
    turno = request.form.get("turnoEliminar")
    curp = request.form.get("curpEliminar")

    if not turno or not curp:
        flash("Debe proporcionar tanto el número de turno como la CURP.", "error")
        return redirect(url_for('eliminar_get'))

    # Llamamos al nuevo método del controlador
    exito = ticket_controller.eliminar_turno_publico(turno, curp)

    if exito:
        flash(f"El Ticket #{turno} ha sido cancelado exitosamente.", "success")
    else:
        flash("No se pudo cancelar el ticket. Verifique que los datos sean correctos y que el ticket esté 'Pendiente'.",
              "error")

    return redirect(url_for('eliminar_get'))


# ---------------------------
# API: Oficinas por municipio
# ---------------------------
@app.get("/api/oficinas")
def api_oficinas():
    id_municipio = request.args.get("id_municipio", type=int)
    if not id_municipio:
        return jsonify([])

    oficinas = ticket_controller.obtener_oficinas_por_municipio(id_municipio)
    oficinas_json = [
        {'id_oficina': o.id_oficina, 'oficina': o.oficina} for o in oficinas
    ]
    return jsonify(oficinas_json)


# ---------------------------
# RUTA DE PDF
# ---------------------------
@app.get("/ticket/pdf/<int:id_turno>/<string:curp>")
def generar_pdf(id_turno, curp):
    datos = ticket_controller.get_datos_comprobante(id_turno, curp)

    if not datos:
        return "Error: Ticket no encontrado o datos incorrectos.", 404

    pdf_bytes = crear_comprobante_rl(datos)

    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f"inline;filename=turno_{datos['numero_turno']}_{curp}.pdf"
        }
    )


# ---------------------------
# Raíz (¡MODIFICADA!)
# ---------------------------
@app.get("/")
def root():
    # Redirigimos a la nueva página de inicio en lugar de renderizar index.html
    return redirect(url_for('inicio'))


if __name__ == "__main__":
    app.run(debug=True)