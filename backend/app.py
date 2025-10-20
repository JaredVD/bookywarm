#Importaciones
from flask import Flask
from flask_sqlalchemy import SQLAlchemy  
from flask_bcrypt import Bcrypt 
from flask import request, jsonify 
import os  # para leer variables de entorno
import requests # para llamar a la API de Google
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity 
# Creamos una instancia de la aplicación Flask
app = Flask(__name__)
bcrypt = Bcrypt(app)  # <-- 2. INICIALIZAR BCRYPT

# --- CONFIGURACIÓN DE LA BASE DE DATOS ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookywarm.db' # <-- 2. CONFIGURAR
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # <-- 3. CONFIGURAR (mejora el rendimiento)
# --- CONFIGURACIÓN DE JWT ---
app.config["JWT_SECRET_KEY"] = os.environ.get('JWT_SECRET_KEY') # <-- 2. CONFIGURAR CLAVE

# --- INICIALIZAR LA BASE DE DATOS ---
db = SQLAlchemy(app) # <-- 4. INICIALIZAR
jwt = JWTManager(app) # <-- 3. INICIALIZAR JWT
# --- DEFINICIÓN DE MODELOS (NUESTRO PLANO) ---

class User(db.Model):
    __tablename__ = 'users'  # Nombre de la tabla
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    # --- ¡NUEVA RELACIÓN! ---
    # Un usuario tiene muchas calificaciones.
    # 'Rating' es el nombre de la CLASE (el modelo).
    # 'back_populates' le dice a SQLAlchemy cómo conectar esto con el modelo Rating.
    ratings = db.relationship('Rating', back_populates='user')

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    google_books_id = db.Column(db.String(100), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150))

    # --- ¡NUEVA RELACIÓN! ---
    # Un libro tiene muchas calificaciones.
    ratings = db.relationship('Rating', back_populates='book')
    
class Rating(db.Model):
    __tablename__ = 'ratings'
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    
    # --- Estas son las "llaves foráneas" (los pasillos) ---
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)

    # --- ¡NUEVAS RELACIONES! ---
    # Una calificación pertenece a UN usuario.
    user = db.relationship('User', back_populates='ratings')
    # Una calificación pertenece a UN libro.
    book = db.relationship('Book', back_populates='ratings')
    
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

    # 5. ¡ÉXITO! Crear el "Pase VIP" (Token)
    # El "identity" es el dato que guardamos dentro del token (su ID)
    # access_token = create_access_token(identity=user.id)
    #corregido
    # Esta es la línea CORRECTA
    access_token = create_access_token(identity=str(user.id))
    
    # 6. Devolver el token al usuario
    return jsonify({
        "mensaje": f"Inicio de sesión exitoso. ¡Bienvenido, {user.username}!",
        "access_token": access_token, # <-- 6. DEVOLVER TOKEN
        "usuario": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }), 200
    
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

# --- RUTA DE PRUEBA PROTEGIDA ---

@app.route("/api/profile", methods=['GET'])
@jwt_required()  # <--- ¡EL GUARDIA DE SEGURIDAD!
def get_profile():
    # 1. Si llegamos aquí, el token es válido.
    # Obtenemos la identidad (el user_id) que guardamos en el token.
    current_user_id = get_jwt_identity()
    
    # 2. Buscamos al usuario en la BD con esa id
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    # 3. Devolvemos la información del usuario
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email
    }), 200    
    
# --- NUEVA RUTA PARA GUARDAR/CALIFICAR UN LIBRO ---
@app.route("/api/books/save", methods=['POST'])
@jwt_required() # <--- ¡PROTEGIDO! Solo usuarios logueados
def save_book():
    # 1. Obtener la ID del usuario desde el token
    current_user_id = get_jwt_identity()
    
    # 2. Obtener los datos del JSON que envía el usuario
    data = request.json
    google_books_id = data.get('google_books_id')
    rating = data.get('rating') # La calificación (ej. 5)

    # (Añadiremos más datos del libro para guardarlos)
    title = data.get('title')
    author = data.get('author') # Esperamos una sola cadena
    
    # 3. Validar los datos
    if not google_books_id or not rating or not title:
        return jsonify({"error": "Faltan datos (google_books_id, rating, title)"}), 400

    # 4. Obtener el User (sabemos que existe por el token)
    user = User.query.get(current_user_id)

    # 5. Buscar si el libro YA existe en nuestra BD (tabla Books)
    book = Book.query.filter_by(google_books_id=google_books_id).first()

    # 6. Si el libro NO existe en nuestra BD, lo creamos
    if not book:
        book = Book(
            google_books_id=google_books_id,
            title=title,
            author=author # Simplificado a una cadena
        )
        db.session.add(book)
        # Hacemos un "commit" parcial para que 'book' obtenga un ID
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Error al guardar nuevo libro", "detalle": str(e)}), 500

    # 7. Verificar si ya existe una calificación de ESTE usuario para ESTE libro
    existing_rating = Rating.query.filter_by(
        user_id=user.id, 
        book_id=book.id
    ).first()

    if existing_rating:
        # Si ya existe, actualizamos la calificación
        existing_rating.rating = rating
        mensaje = "Calificación actualizada"
    else:
        # Si no existe, creamos la nueva calificación (Rating)
        new_rating = Rating(
            rating=rating,
            user_id=user.id,
            book_id=book.id
        )
        db.session.add(new_rating)
        mensaje = "Libro guardado y calificado"

    # 8. Guardar los cambios finales en la BD
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al guardar calificación", "detalle": str(e)}), 500

    return jsonify({"mensaje": mensaje, "book_id": book.id}), 201