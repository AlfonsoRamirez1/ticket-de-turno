# app.py
import time
from datetime import datetime
from flask import (Flask, render_template, request, jsonify, abort,
                   session, redirect, url_for, flash, Response)
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
import random

# Controladores
from controllers.ticket_controller import TicketController
from controllers.auth_controller import AuthController
from config import Config
from utils.pdf_rl import crear_comprobante_rl

# --- INICIO DE MODIFICACIÓN (REQ 5) ---
from controllers.catalogo_controller import CatalogoController  # Importar el nuevo controlador

# --- FIN DE MODIFICACIÓN ---

app = Flask(__name__)
app.config.from_object(Config)

# --- CONFIGURACIÓN DE FLASK-LOGIN ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_get'
login_manager.login_message = 'Por favor, inicie sesión para acceder a esta página.'
login_manager.login_message_category = 'error'

# Instanciamos controladores
ticket_controller = TicketController()
auth_controller = AuthController()

# --- INICIO DE MODIFICACIÓN (REQ 5) ---
catalogo_controller = CatalogoController()  # Instanciar el nuevo controlador


# --- FIN DE MODIFICACIÓN ---


@login_manager.user_loader
def load_user(user_id):
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
    password = request.form.get('password')
    captcha_input = request.form.get('captcha')

    try:
        if 'captcha_answer' not in session or int(captcha_input) != session['captcha_answer']:
            flash('Respuesta incorrecta del Captcha.', 'error')
            return redirect(url_for('login_get'))
    except (ValueError, TypeError):
        flash('Respuesta de Captcha inválida.', 'error')
        return redirect(url_for('login_get'))

    admin = auth_controller.validar_login(usuario, password)

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
# RUTAS DE ADMINISTRACIÓN (PROTEGIDAS)
# ---------------------------

@app.get("/admin/turnos")
@login_required
def admin_turnos_get():
    # "q" es el parámetro de búsqueda
    query = request.args.get("q", "")
    # "vista" define si vemos 'activos' (default) o 'cancelados'
    vista = request.args.get("vista", "activos")

    # Pasamos ambos parámetros al controlador
    turnos = ticket_controller.buscar_turnos_admin(query, vista)

    # Pasamos 'vista' y 'query' a la plantilla para los enlaces y el form
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

    # Mantenemos la vista actual después de la acción
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

    # Mantenemos la vista actual después de la acción
    vista = request.args.get("vista", "activos")
    return redirect(url_for('admin_turnos_get', vista=vista))


# --- INICIO DE NUEVAS RUTAS (REQ 4) ---

@app.get("/admin/turnos/crear")
@login_required
def admin_crear_get():
    """ Muestra el formulario para que el admin cree un turno. """
    municipios = ticket_controller.obtener_municipios()
    niveles = ticket_controller.obtener_niveles()
    asuntos = ticket_controller.obtener_asuntos()
    # Reutilizamos los mismos catálogos que la vista pública
    return render_template("admin_crear_turno.html",
                           municipios=municipios,
                           niveles=niveles,
                           asuntos=asuntos)


@app.post("/admin/turnos/crear")
@login_required
def admin_crear_post():
    """ Procesa el formulario de creación del admin. """
    datos_formulario = request.form
    nuevo_turno = ticket_controller.crear_turno(datos_formulario)
    if nuevo_turno:
        flash(f"Turno #{nuevo_turno.numero_turno} creado exitosamente para {nuevo_turno.solicitante.curp}.", "success")
        return redirect(url_for('admin_turnos_get'))
    else:
        flash("Error al crear el turno. Verifique los datos.", "error")
        # Recargamos la página de creación para que el admin corrija
        return redirect(url_for('admin_crear_get'))


@app.get("/admin/turnos/editar/<int:id_turno>")
@login_required
def admin_editar_get(id_turno):
    """ Muestra el formulario para editar un turno específico. """
    # Usamos el nuevo método del controlador que busca por ID
    data = ticket_controller.buscar_turno_admin_para_editar(id_turno)

    if data:
        return render_template("admin_editar_turno.html",
                               ticket=data['ticket'],
                               catalogos=data['catalogos'],
                               vista=request.args.get("vista", "activos"))  # Pasamos la vista
    else:
        flash("Ticket no encontrado.", 'error')
        return redirect(url_for('admin_turnos_get'))


@app.post("/admin/turnos/editar")
@login_required
def admin_editar_post():
    """ Guarda los cambios del formulario de edición del admin. """
    # Reutilizamos la lógica de actualización
    exito = ticket_controller.actualizar_turno(request.form)
    if exito:
        flash("¡Ticket actualizado con éxito!", 'success')
    else:
        flash("Error al actualizar el ticket. Intente de nuevo.", 'error')

    # Mantenemos la vista actual después de la acción
    vista = request.form.get("vista", "activos")
    return redirect(url_for('admin_turnos_get', vista=vista))


# --- FIN DE NUEVAS RUTAS (REQ 4) ---


# ---------------------------
# RUTAS CRUD CATÁLOGOS (REQ 5)
# ---------------------------

@app.get("/admin/catalogos")
@login_required
def admin_catalogos_menu():
    """ Muestra el menú principal de catálogos. """
    return render_template("admin_catalogos_menu.html")


# --- RUTAS PARA MUNICIPIOS ---

@app.get("/admin/catalogos/municipios")
@login_required
def admin_municipios_get():
    """ Muestra la lista de municipios (Leer). """
    municipios = catalogo_controller.get_municipios()
    return render_template("admin_cat_municipios.html", municipios=municipios)


@app.post("/admin/catalogos/municipios/crear")
@login_required
def admin_municipios_crear():
    """ Procesa la creación de un nuevo municipio (Crear). """
    nombre = request.form.get("nombre")
    exito, mensaje = catalogo_controller.crear_municipio(nombre)
    flash(mensaje, "success" if exito else "error")
    return redirect(url_for('admin_municipios_get'))


@app.get("/admin/catalogos/municipios/editar/<int:id_municipio>")
@login_required
def admin_municipios_editar_get(id_municipio):
    """ Muestra el formulario para editar un municipio. """
    municipio = catalogo_controller.get_municipio_by_id(id_municipio)
    if not municipio:
        flash("Municipio no encontrado.", "error")
        return redirect(url_for('admin_municipios_get'))
    return render_template("admin_cat_municipio_editar.html", municipio=municipio)


@app.post("/admin/catalogos/municipios/editar")
@login_required
def admin_municipios_editar_post():
    """ Procesa la actualización de un municipio (Actualizar). """
    id_municipio = request.form.get("id_municipio")
    nombre = request.form.get("nombre")
    exito, mensaje = catalogo_controller.actualizar_municipio(id_municipio, nombre)
    flash(mensaje, "success" if exito else "error")
    return redirect(url_for('admin_municipios_get'))


@app.post("/admin/catalogos/municipios/eliminar")
@login_required
def admin_municipios_eliminar():
    """ Procesa la eliminación de un municipio (Eliminar). """
    id_municipio = request.form.get("id_municipio")
    exito, mensaje = catalogo_controller.eliminar_municipio(id_municipio)
    flash(mensaje, "success" if exito else "error")
    return redirect(url_for('admin_municipios_get'))


# --- Aquí irán las rutas para Asuntos, Niveles y Oficinas ---


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
        return "Error al crear el turno.", 500


@app.get("/ver")
def ver_get():
    turno = request.args.get("turno")
    curp = request.args.get("curp")
    ticket_encontrado = None
    mensaje_error = None
    if turno and curp:
        ticket_encontrado = ticket_controller.buscar_turno(turno, curp)
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
    exito = True  # Simulado
    mensaje = f"Ticket {turno} eliminado correctamente ✅" if exito else f"Error al eliminar ticket {turno}"
    return render_template("eliminarTicket.html", mensaje_eliminar=mensaje)


# ---------------------------
# API: Oficinas por municipio
# ---------------------------
@app.get("/api/oficinas")
def api_oficinas():
    id_municipio = request.args.get("id_municipio", type=int)
    if not id_municipio:
        return jsonify([])
    oficinas = ticket_controller.obtener_oficinas_por_municipio(id_municipio)
    return jsonify(oficinas)


# ---------------------------
# RUTA DE PDF (AHORA USA REPORTLAB)
# ---------------------------
@app.get("/ticket/pdf/<int:id_turno>/<string:curp>")
def generar_pdf(id_turno, curp):
    datos = ticket_controller.get_datos_comprobante(id_turno, curp)

    if not datos:
        return "Error: Ticket no encontrado o datos incorrectos.", 404

    # --- INICIO DE LA MODIFICACIÓN ---
    # Quitamos el try...except para ver el error real
    # y llamamos a la nueva función
    pdf_bytes = crear_comprobante_rl(datos)
    # --- FIN DE LA MODIFICACIÓN ---

    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f"inline;filename=turno_{datos['numero_turno']}_{curp}.pdf"
        }
    )


# ---------------------------
# Raíz
# ---------------------------
@app.get("/")
def root():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)