from flask import Flask
from flask_sqlalchemy import SQLAlchemy  # <-- 1. IMPORTAR
from flask_bcrypt import Bcrypt  # <-- 1. IMPORTAR BCRYPT
from flask import request, jsonify # <-- AÑADE ESTO AL BLOQUE DE IMPORTS DE FLASK

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

# --- API DE USUARIOS ---

@app.route("/api/register", methods=['POST'])
def register_user():
    # 1. Obtener los datos JSON que nos envía el cliente (Postman)
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # 2. Validar que recibimos todos los datos
    if not username or not email or not password:
        # 400 = Bad Request (Petición incorrecta)
        return jsonify({"error": "Faltan datos (username, email, password)"}), 400

    # 3. Verificar si el usuario o email ya existen en la BD
    if User.query.filter_by(email=email).first():
        # 409 = Conflict (El recurso ya existe)
        return jsonify({"error": "El email ya está registrado"}), 409
    
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "El nombre de usuario ya está en uso"}), 409

    # 4. Hashear la contraseña para guardarla de forma segura
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    # 5. Crear el nuevo usuario con el modelo
    nuevo_usuario = User(
        username=username, 
        email=email, 
        password_hash=hashed_password
    )
    
    # 6. Guardar el usuario en la base de datos
    try:
        db.session.add(nuevo_usuario)
        db.session.commit()
    except Exception as e:
        db.session.rollback() # Revertir cambios si algo sale mal
        return jsonify({"error": "Error al guardar en la base de datos", "detalle": str(e)}), 500 # 500 = Error interno

    # 7. Enviar una respuesta de éxito
    # 201 = Created (Se creó un nuevo recurso)
    return jsonify({
        "mensaje": f"Usuario '{username}' creado exitosamente",
        "usuario": {
            "id": nuevo_usuario.id,
            "username": nuevo_usuario.username,
            "email": nuevo_usuario.email
        }
    }), 201