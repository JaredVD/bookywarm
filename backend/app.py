from flask import Flask
from flask_sqlalchemy import SQLAlchemy  # <-- 1. IMPORTAR
from flask_bcrypt import Bcrypt  # <-- 1. IMPORTAR BCRYPT
from flask import request, jsonify # <-- AÑADE ESTO AL BLOQUE DE IMPORTS DE FLASK
import os  # <-- AÑADE ESTO, para leer variables de entorno
import requests # <-- AÑADE ESTO, para llamar a la API de Google

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

# --Registro de usuario
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
    
#--Login de usuario
@app.route("/api/login", methods=['POST'])
def login_user():
    # 1. Obtener los datos JSON
    data = request.json
    email = data.get('email')
    password = data.get('password')

    # 2. Validar que recibimos todo
    if not email or not password:
        return jsonify({"error": "Faltan datos (email, password)"}), 400

    # 3. Buscar al usuario por email
    user = User.query.filter_by(email=email).first()

    # 4. Si el usuario no existe O la contraseña no coincide...
    # Usamos bcrypt.check_password_hash() para comparar
    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        # 401 = Unauthorized (No autorizado)
        return jsonify({"error": "Email o contraseña incorrectos"}), 401

    # 5. Si todo es correcto, enviamos respuesta de éxito
    return jsonify({
        "mensaje": f"Inicio de sesión exitoso. ¡Bienvenido, {user.username}!",
        "usuario": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }), 200 # 200 = OK
    
# --- API DE LIBROS ---

@app.route("/api/books/search", methods=['GET'])
def search_books():
    # 1. Obtener el término de búsqueda de los parámetros de la URL (ej: ?q=dune)
    query = request.args.get('q')
    
    if not query:
        return jsonify({"error": "Se requiere un parámetro de búsqueda 'q'"}), 400

    # 2. Obtener la clave de API de forma segura desde el .env
    api_key = os.environ.get('GOOGLE_BOOKS_API_KEY')
    if not api_key:
        return jsonify({"error": "Clave de API de Google Books no configurada"}), 500

    # 3. Construir la URL para la API de Google Books
    google_api_url = f"https://www.googleapis.com/books/v1/volumes?q={query}&key={api_key}"

    # 4. Hacer la petición a la API de Google
    try:
        response = requests.get(google_api_url)
        response.raise_for_status() # Lanza un error si la petición falló (ej. 404, 500)
        data = response.json() # Convertir la respuesta de Google a JSON

        # 5. (Opcional pero recomendado) Limpiar y formatear la respuesta
        # El JSON de Google es enorme. Vamos a devolver solo lo que necesitamos.
        libros_encontrados = []
        if 'items' in data:
            for item in data['items']:
                info = item.get('volumeInfo', {})
                libros_encontrados.append({
                    "google_books_id": item.get('id'),
                    "title": info.get('title'),
                    "authors": info.get('authors', []), # Autores es una lista
                    "published_date": info.get('publishedDate'),
                    "description": info.get('description'),
                    "cover_image": info.get('imageLinks', {}).get('thumbnail')
                })

        return jsonify(libros_encontrados), 200

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Error al contactar la API de Google", "detalle": str(e)}), 503