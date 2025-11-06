# db.py
from flask_sqlalchemy import SQLAlchemy

# Esta es la instancia del ORM que usarán todos nuestros archivos.
# Es el nuevo "Singleton" de base de datos.
db = SQLAlchemy()