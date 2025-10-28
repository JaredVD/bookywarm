#Importaciones
from flask import Flask
from flask_sqlalchemy import SQLAlchemy  
from flask_bcrypt import Bcrypt 
from flask import request, jsonify 
import os  # para leer variables de entorno. Nos da acceso al sistema operativo incluyendo las variables de entorno
import requests # para llamar a la API de Google
from flask_cors import CORS # <-- 1. IMPORTAR CORS (por ahora permitirá cualquier origen)
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity 

app = Flask(__name__)# Creamos una instancia de la aplicación Flask
bcrypt = Bcrypt(app)  # Inicializamos BCRYPT

# --- CONFIGURACIÓN DE CORS ---
# Permitir peticiones de cualquier origen (temporalmente para desarrollo)
CORS(app) # <-- 2. INICIALIZAR CORS

# CONFIGURACIÓN DE LA BASE DE DATOS 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookywarm.db' # Configuracion
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Para mejorar el rendimiento
# --- CONFIGURACIÓN DE JWT ---
app.config["JWT_SECRET_KEY"] = os.environ.get('JWT_SECRET_KEY') # Configuracion de clave

# INICIALIZAR VARIABLES
db = SQLAlchemy(app) # Inicializar base de datos
jwt = JWTManager(app) # inicializar jwt

#Tablas de bases de datos

#Tabla de usuarios
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    # --- Nueva Relacion---
    # Un usuario tiene muchas calificaciones.
    # 'Rating' es el nombre de la CLASE (el modelo).
    # 'back_populates' le dice a SQLAlchemy cómo conectar esto con el modelo Rating.
    ratings = db.relationship('Rating', back_populates='user')

#Tabla de libros
class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    google_books_id = db.Column(db.String(100), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150))

    # --- ¡LÍNEA NUEVA! ---
    cover_image_url = db.Column(db.String(500), nullable=True) # URL de la portada
    
    # --- Nueva Relacion---
    # Un libro tiene muchas calificaciones.
    ratings = db.relationship('Rating', back_populates='book')
    
#Tabla de calificación
class Rating(db.Model):
    __tablename__ = 'ratings'
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    
    # --- Estas son las "llaves foráneas" (los pasillos) ---
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)

    # --- Nueva Relacion---
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
        db.session.commit()#guarda al usuario nuevo en la base de datos
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
    access_token = create_access_token(identity=str(user.id)) #convertimos el id que es int en un string, es importante ya que JWT prefiere que la identidad del usuario (id) se guarde como string
    
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
    
    # --- NUEVA RUTA PARA VER LOS LIBROS GUARDADOS DEL USUARIO ---
@app.route("/api/my-books", methods=['GET'])
@jwt_required() # <--- ¡PROTEGIDO!
def get_my_books():
    # 1. Obtenemos la identidad del usuario desde el token
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    # 2. ¡LA MAGIA DE LA MISIÓN #15!
    # Simplemente accedemos a 'user.ratings'
    # 'user.ratings' es una lista de objetos 'Rating'
    libros_guardados = []
    for rating in user.ratings:
        # Para cada objeto 'Rating', accedemos a su 'libro' y 'calificación'
        # Esto es posible gracias a 'db.relationship'
        libros_guardados.append({
            "rating_id": rating.id,
            "rating": rating.rating,
            "book": {
                "id": rating.book.id,
                "google_books_id": rating.book.google_books_id,
                "title": rating.book.title,
                "author": rating.book.author,
                "cover_image_url": rating.book.cover_image_url # <-- ¡ESTA ES LA LÍNEA QUE FALTABA!
            }
        })

    # 3. Devolvemos la lista de libros y calificaciones
    return jsonify(libros_guardados), 200

# --- API DE LIBROS ---
@app.route("/api/books/search", methods=['GET'])
def search_books():
    # 1. lo siguiente lee los parametros de la url despues del ? (ej: ?q=dune)
    query = request.args.get('q')
    
    if not query:
        return jsonify({"error": "Se requiere un parámetro de búsqueda 'q'"}), 400

    # 2. Obtener la clave de API de Google books de forma segura desde el .env
    api_key = os.environ.get('GOOGLE_BOOKS_API_KEY')
    if not api_key:
        return jsonify({"error": "Clave de API de Google Books no configurada"}), 500

    # 3. Construir la URL para la API de Google Books
    google_api_url = f"https://www.googleapis.com/books/v1/volumes?q={query}&key={api_key}"

    # 4. Hacer la petición a la API de Google
    try:
        response = requests.get(google_api_url) #con esto hacemos una peticioin get
        response.raise_for_status() # Lanza un error si la petición falló (ej. 404, 500)
        data = response.json() # Convertir la respuesta de Google a JSON

        # 5. (Opcional pero recomendado) Limpiar y formatear la respuesta
        # El JSON de Google es enorme. Vamos a devolver solo lo que necesitamos.
        libros_encontrados = []
        if 'items' in data:
            for item in data['items']:#con el siguiente for devolvemos solo la información que queremos
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
@jwt_required()  # <--- ¡EL GUARDIA DE SEGURIDAD! valida si el token es valido
def get_profile():
    # 1. Si llegamos aquí, el token es válido.
    # Obtenemos la identidad (el user_id) que guardamos en el token.
    current_user_id = get_jwt_identity() #get_jwt_identity() extrae el id del usuario.
    
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
    cover_image_url = data.get('cover_image_url') # <-- ¡LÍNEA NUEVA!
    
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
            author=author, # Simplificado a una cadena
            cover_image_url=cover_image_url # <-- ¡LÍNEA NUEVA!
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

@app.route("/api/ratings/<int:rating_id>", methods=['PUT']) #PUT es el método HTTP estándar para actualizar un recurso existente
#<int:rating_id> Esta es una ruta dinamica. Le decimos a Flask que espere un número en la URL (el ID de la calificación que queremos cambiar), ahi irá el id del libro que tengas guardado y calificado
@jwt_required()
def update_rating(rating_id):
    # 1. Obtenemos la identidad del usuario desde el token
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id) # Obtenemos el objeto User

    # 2. Buscamos la calificación específica por su ID
    rating_to_update = Rating.query.get(rating_id)

    # 3. Validaciones de seguridad
    if not rating_to_update:
        return jsonify({"error": "Calificación no encontrada"}), 404

    # ¡MUY IMPORTANTE! Verificar que el usuario es dueño de esta calificación
    if rating_to_update.user_id != user.id:
        return jsonify({"error": "No autorizado para modificar esta calificación"}), 403 # 403 = Forbidden

    # 4. Obtener la nueva calificación del JSON
    data = request.json
    new_rating_value = data.get('rating')

    if not new_rating_value:
        return jsonify({"error": "Falta el campo 'rating'"}), 400

    # 5. Actualizar el valor y guardar en la BD
    try:
        rating_to_update.rating = new_rating_value
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar la calificación", "detalle": str(e)}), 500

    # 6. Devolver la calificación actualizada
    return jsonify({
        "mensaje": "Calificación actualizada exitosamente",
        "rating": {
            "id": rating_to_update.id,
            "book_id": rating_to_update.book_id,
            "rating": rating_to_update.rating
        }
    }), 200
    
    # --- NUEVA RUTA PARA ELIMINAR UNA CALIFICACIÓN ---
@app.route("/api/ratings/<int:rating_id>", methods=['DELETE'])
@jwt_required()
def delete_rating(rating_id):
    # 1. Obtenemos la identidad del usuario desde el token
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    # 2. Buscamos la calificación específica por su ID
    rating_to_delete = Rating.query.get(rating_id)

    # 3. Validaciones de seguridad
    if not rating_to_delete:
        return jsonify({"error": "Calificación no encontrada"}), 404

    # 4. ¡MUY IMPORTANTE! Verificar que el usuario es dueño de esta calificación
    if rating_to_delete.user_id != user.id:
        return jsonify({"error": "No autorizado para eliminar esta calificación"}), 403 # 403 = Forbidden

    # 5. Eliminar el objeto de la sesión de la BD
    try:
        db.session.delete(rating_to_delete)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar la calificación", "detalle": str(e)}), 500

    # 6. Devolver una respuesta de éxito (sin contenido)
    return jsonify({"mensaje": "Calificación eliminada exitosamente"}), 200 # 200 OK o 204 No Content