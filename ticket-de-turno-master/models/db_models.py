# models/db_models.py
from db import db  # Importamos la instancia de la BD
from flask_login import UserMixin
from datetime import datetime

# --- INICIO DE CORRECCIÓN ---
# Importamos el tipo TINYINT específico del dialecto de MySQL
from sqlalchemy.dialects.mysql import TINYINT


# --- FIN DE CORRECCIÓN ---


# --- MODELOS DE CATÁLOGOS ---
#
class Municipios(db.Model):
    __tablename__ = 'municipios'
    id_municipio = db.Column(db.SmallInteger, primary_key=True, autoincrement=True)
    municipio = db.Column(db.String(100), nullable=False, unique=True)

    # Relaciones (un municipio tiene muchas oficinas y un contador)
    oficinas = db.relationship('OficinasRegionales', back_populates='municipio')
    contador = db.relationship('ContadorTurnos', back_populates='municipio', uselist=False)


#
class NivelesEducativos(db.Model):
    __tablename__ = 'niveles_educativos'

    # --- INICIO DE CORRECCIÓN ---
    # Usamos TINYINT(unsigned=True) en lugar de db.TinyInteger
    id_nivel = db.Column(TINYINT(unsigned=True), primary_key=True, autoincrement=True)
    # --- FIN DE CORRECCIÓN ---

    nivel = db.Column(db.String(60), nullable=False, unique=True)

    turnos = db.relationship('Turnos', back_populates='nivel')


#
class Asuntos(db.Model):
    __tablename__ = 'asuntos'
    id_asunto = db.Column(db.SmallInteger, primary_key=True, autoincrement=True)
    descripcion = db.Column(db.String(200), nullable=False, unique=True)

    turnos = db.relationship('Turnos', back_populates='asunto')


#
class OficinasRegionales(db.Model):
    __tablename__ = 'oficinas_regionales'
    id_oficina = db.Column(db.SmallInteger, primary_key=True, autoincrement=True)
    oficina = db.Column(db.String(150), nullable=False)
    id_municipio = db.Column(db.SmallInteger, db.ForeignKey('municipios.id_municipio'), nullable=False)

    # Relaciones (una oficina pertenece a un municipio y tiene muchos turnos)
    municipio = db.relationship('Municipios', back_populates='oficinas')
    turnos = db.relationship('Turnos', back_populates='oficina')

    # --- NUEVA RELACIÓN ---
    horarios = db.relationship('HorariosAtencion', back_populates='oficina', cascade="all, delete-orphan")
    # --- FIN DE NUEVA RELACIÓN ---


# --- MODELO NUEVO ---
class HorariosAtencion(db.Model):
    __tablename__ = 'horarios_atencion'
    id_horario = db.Column(db.SmallInteger, primary_key=True, autoincrement=True)
    id_oficina = db.Column(db.SmallInteger, db.ForeignKey('oficinas_regionales.id_oficina'), nullable=False)
    dia_semana = db.Column(db.Enum('lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo'),
                           nullable=False)
    hora_apertura = db.Column(db.Time, nullable=False)
    hora_cierre = db.Column(db.Time, nullable=False)
    max_turnos_dia = db.Column(db.SmallInteger, default=50, nullable=False)

    # Relación (un horario pertenece a una oficina)
    oficina = db.relationship('OficinasRegionales', back_populates='horarios')

    # --- Constraint para evitar duplicados (opcional pero recomendado) ---
    __table_args__ = (
        db.UniqueConstraint('id_oficina', 'dia_semana', name='uq_oficina_dia'),
    )


# --- FIN DE MODELO NUEVO ---


# --- MODELOS DE CONTROL ---

#
class ContadorTurnos(db.Model):
    __tablename__ = 'contador_turnos'
    id_municipio = db.Column(db.SmallInteger, db.ForeignKey('municipios.id_municipio'), primary_key=True)
    ultimo_turno = db.Column(db.SmallInteger, default=0)
    fecha_ultimo_turno = db.Column(db.Date, nullable=True)

    # Relación (un contador pertenece a un municipio)
    municipio = db.relationship('Municipios', back_populates='contador')


#
class Administradores(db.Model, UserMixin):  # Heredamos de UserMixin para Flask-Login
    __tablename__ = 'administradores'
    id_admin = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(60), nullable=False)  # El hash es de 60 chars
    nombre = db.Column(db.String(150), nullable=False)
    rol = db.Column(db.Enum('admin', 'usuario'), default='usuario')

    # Implementación para UserMixin de Flask-Login
    def get_id(self):
        return str(self.id_admin)


# --- MODELOS DE DATOS ---

#
class Solicitantes(db.Model):
    __tablename__ = 'solicitantes'
    id_solicitante = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_tramitante = db.Column(db.String(120), nullable=False)
    nombre_solicitante = db.Column(db.String(100), nullable=False)
    paterno_solicitante = db.Column(db.String(60), nullable=False)
    materno_solicitante = db.Column(db.String(60))
    curp = db.Column(db.String(18), nullable=False, unique=True, index=True)
    telefono = db.Column(db.String(10))
    celular = db.Column(db.String(10), nullable=False)
    correo = db.Column(db.String(150))
    fecha_registro = db.Column(db.TIMESTAMP, default=datetime.now)

    turnos = db.relationship('Turnos', back_populates='solicitante')


#
class Turnos(db.Model):
    __tablename__ = 'turnos'
    id_turno = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_solicitante = db.Column(db.Integer, db.ForeignKey('solicitantes.id_solicitante'), nullable=False)
    id_oficina = db.Column(db.SmallInteger, db.ForeignKey('oficinas_regionales.id_oficina'), nullable=False)
    numero_turno = db.Column(db.SmallInteger, nullable=False)

    # --- CAMPOS MODIFICADOS ---
    # Almacena la fecha Y hora de la CITA
    fecha_solicitud = db.Column(db.TIMESTAMP, nullable=False)
    # Almacena solo la HORA de la CITA (para facilitar queries)
    hora_solicitud = db.Column(db.Time, nullable=False)
    # --- FIN DE MODIFICACIÓN ---

    # --- INICIO DE CORRECCIÓN ---
    # Usamos TINYINT(unsigned=True) aquí también
    id_nivel = db.Column(TINYINT(unsigned=True), db.ForeignKey('niveles_educativos.id_nivel'), nullable=False)
    # --- FIN DE CORRECCIÓN ---

    id_asunto = db.Column(db.SmallInteger, db.ForeignKey('asuntos.id_asunto'), nullable=False)
    estado = db.Column(db.Enum('pendiente', 'resuelto', 'cancelado'), default='pendiente')
    codigo_qr = db.Column(db.String(255), nullable=False, unique=True)  # Usaremos la CURP aquí
    observaciones = db.Column(db.Text, nullable=True)

    # --- ¡LA MAGIA DEL ORM! ---
    solicitante = db.relationship('Solicitantes', back_populates='turnos')
    oficina = db.relationship('OficinasRegionales', back_populates='turnos')
    nivel = db.relationship('NivelesEducativos', back_populates='turnos')
    asunto = db.relationship('Asuntos', back_populates='turnos')