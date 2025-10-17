from flask import Flask
from flask_sqlalchemy import SQLAlchemy  # <-- 1. IMPORTAR
from flask_bcrypt import Bcrypt  # <-- 1. IMPORTAR BCRYPT

# Creamos una instancia de la aplicación Flask
app = Flask(__name__)
bcrypt = Bcrypt(app)  # <-- 2. INICIALIZAR BCRYPT

# --- CONFIGURACIÓN DE LA BASE DE DATOS ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookywarm.db' # <-- 2. CONFIGURAR
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # <-- 3. CONFIGURAR (mejora el rendimiento)

# --- INICIALIZAR LA BASE DE DATOS ---
db = SQLAlchemy(app) # <-- 4. INICIALIZAR

# --- DEFINICIÓN DE MODELOS (NUESTRO PLANO) ---

class User(db.Model):
    __tablename__ = 'users'  # Nombre de la tabla
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    google_books_id = db.Column(db.String(100), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150))

class Rating(db.Model):
    __tablename__ = 'ratings'
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    
    # --- Estas son las "llaves foráneas" (los pasillos) ---
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)

# --- RUTAS ---
@app.route("/")
def home():
    return "¡Hola, mundo desde Flask!"