import os
import json
import uuid 
from functools import wraps
from datetime import timedelta 
from flask import Flask, request, jsonify, session, send_from_directory, redirect, url_for, render_template
from flask_session import Session
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename 

# --- Configuración de la App ---
app = Flask(__name__) 

# --- ¡NUEVA SECCIÓN DE CONFIGURACIÓN DE RUTAS! ---
# 1. Definir el directorio de datos.
#    Render nos da una variable 'RENDER_DISK_PATH'. Si no existe (local), usa la carpeta actual ('.')
DATA_DIR = os.environ.get('RENDER_DISK_PATH', '.')

# 2. Definir rutas de bases de datos usando DATA_DIR
USER_DB_PATH = os.path.join(DATA_DIR, 'user.json') 
PRODUCT_DB_PATH = os.path.join(DATA_DIR, 'products.json') 

# 3. Definir ruta de subidas
#    Las subidas DEBEN estar dentro de 'static' para que se puedan servir,
#    así que creamos una ruta persistente DENTRO de static.
STATIC_DIR = os.path.join(app.root_path, 'static')
UPLOAD_FOLDER = os.path.join(STATIC_DIR, 'uploads_persistent')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# --- FIN DE LA NUEVA SECCIÓN ---

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config['SECRET_KEY'] = 'tu_clave_secreta_de_sesion_aqui'
app.config['SESSION_TYPE'] = 'filesystem'
# La carpeta de sesión TAMBIÉN debe ser persistente
app.config['SESSION_FILE_DIR'] = os.path.join(DATA_DIR, 'flask_session') 
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30) 
Session(app)
bcrypt = Bcrypt(app)

REGISTRATION_SECRET_KEY = 'root' 

# --- Función de Timeout (Sin cambios) ---
@app.before_request
def make_session_permanent():
    session.permanent = True

# --- Funciones de "Base de Datos" (Sin cambios, ya usan las variables nuevas) ---
def read_users():
    if not os.path.exists(USER_DB_PATH): return []
    try:
        with open(USER_DB_PATH, 'r') as f: return json.load(f)
    except json.JSONDecodeError: return []
def write_users(users):
    with open(USER_DB_PATH, 'w') as f: json.dump(users, f, indent=2)

def read_products():
    if not os.path.exists(PRODUCT_DB_PATH): return []
    try:
        with open(PRODUCT_DB_PATH, 'r') as f: return json.load(f)
    except json.JSONDecodeError: return []
def write_products(products):
    with open(PRODUCT_DB_PATH, 'w') as f: json.dump(products, f, indent=2)

# --- Funciones de Archivos (MODIFICADA) ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file):
    if file and allowed_file(file.filename):
        filename_secure = secure_filename(file.filename)
        ext = filename_secure.rsplit('.', 1)[1]
        unique_filename = f"{uuid.uuid4()}.{ext}"
        
        # Asegurarse de que el directorio de subida exista
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        # ¡CAMBIO! La URL pública sigue siendo /static/, pero la carpeta es la nueva
        return f"/static/uploads_persistent/{unique_filename}"
    return None

# --- Decoradores de Autenticación (Sin cambios) ---
# ... (tu decorador @is_admin) ...
def is_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # ... (código existente)
        if 'user' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Sesión expirada.'}), 401
            return redirect(url_for('login_page')) 
        if session['user'].get('role') != 'admin':
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Acceso prohibido.'}), 403
            return '<h1>403 - Acceso Prohibido</h1>', 403
        return f(*args, **kwargs)
    return decorated_function


# --- Rutas de Autenticación (Sin cambios) ---
# ... (@app.route('/api/register'), @app.route('/api/login'), @app.route('/api/logout')) ...
@app.route('/api/register', methods=['POST'])
def api_register():
    # ... (código existente)
    data = request.json
    username = data.get('username')
    password = data.get('password')
    secret_key = data.get('secret_key')
    if secret_key != REGISTRATION_SECRET_KEY: return jsonify({'error': 'Clave secreta incorrecta.'}), 403
    if not username or not password: return jsonify({'error': 'Faltan campos.'}), 400
    users = read_users()
    if any(u['username'] == username for u in users): return jsonify({'error': 'El nombre de usuario ya existe.'}), 409
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = {'username': username, 'password': hashed_password, 'role': 'admin'}
    users.append(new_user)
    write_users(users)
    return jsonify({'message': 'Administrador registrado.'}), 201

@app.route('/api/login', methods=['POST'])
def api_login():
    # ... (código existente)
    data = request.json
    username = data.get('username')
    password = data.get('password')
    users = read_users()
    user = next((u for u in users if u['username'] == username), None)
    if user and bcrypt.check_password_hash(user['password'], password):
        session['user'] = {'username': user['username'], 'role': user['role']}
        return jsonify({'message': 'Login exitoso', 'role': user['role']})
    else:
        return jsonify({'message': 'Usuario o contraseña incorrectos.'}), 401

@app.route('/api/logout')
def api_logout():
    session.pop('user', None)
    return redirect(url_for('login_page'))


# --- Rutas CRUD (Sin cambios en la lógica, solo usan las variables nuevas) ---
# ... (@app.route('/api/products') GET, POST, PUT, DELETE) ...
@app.route('/api/products', methods=['GET'])
def get_products():
    products = read_products()
    return jsonify(products)

@app.route('/api/products/<string:product_id>', methods=['GET'])
@is_admin 
def get_product(product_id):
    products = read_products()
    product = next((p for p in products if p['id'] == product_id), None)
    if product: return jsonify(product)
    return jsonify({'error': 'Producto no encontrado'}), 404

@app.route('/api/products', methods=['POST'])
@is_admin
def create_product():
    # ... (código existente)
    try:
        data = request.form
        img_url = None
        if 'img_file' in request.files:
            file = request.files['img_file']
            if file.filename != '': img_url = save_image(file)
        try: price_float = float(data.get('price', '0'))
        except ValueError: price_float = 0.0
        new_product = { 'id': str(uuid.uuid4()), 'name': data.get('name'), 'category': data.get('category'), 'price': price_float, 'img': img_url, 'stock': data.get('stock') == 'true', 'sizes': [size.strip() for size in data.get('sizes').split(',') if size.strip()] }
        products = read_products()
        products.append(new_product)
        write_products(products)
        return jsonify(new_product), 201
    except Exception as e:
        return jsonify({'error': 'Error interno.', 'details': str(e)}), 500

@app.route('/api/products/<string:product_id>', methods=['PUT'])
@is_admin
def update_product(product_id):
    # ... (código existente)
    try:
        data = request.form
        products = read_products()
        product = next((p for p in products if p['id'] == product_id), None)
        if not product: return jsonify({'error': 'Producto no encontrado'}), 404
        img_url = data.get('img_url') 
        if 'img_file' in request.files:
            file = request.files['img_file']
            if file.filename != '':
                new_img_url = save_image(file)
                if new_img_url: img_url = new_img_url
        try: price_float = float(data.get('price', '0'))
        except ValueError: price_float = product.get('price', 0.0)
        product['name'] = data.get('name')
        product['category'] = data.get('category')
        product['price'] = price_float
        product['img'] = img_url
        product['stock'] = data.get('stock') == 'true'
        product['sizes'] = [size.strip() for size in data.get('sizes').split(',') if size.strip()]
        write_products(products)
        return jsonify(product)
    except Exception as e:
        return jsonify({'error': 'Error interno.', 'details': str(e)}), 500

@app.route('/api/products/<string:product_id>', methods=['DELETE'])
@is_admin
def delete_product(product_id):
    # ... (código existente)
    products = read_products()
    new_products = [p for p in products if p['id'] != product_id]
    if len(new_products) == len(products): return jsonify({'error': 'Producto no encontrado'}), 404
    write_products(new_products)
    return jsonify({'message': 'Producto eliminado'}), 200

# --- Rutas para servir HTML (Sin cambios) ---
@app.route('/')
def login_page():
    return render_template('index.html')

@app.route('/admin')
@app.route('/admin.html')
@is_admin 
def admin_page():
    return render_template('admin.html')

@app.route('/register')
@app.route('/register.html')
def register_page():
    return render_template('register.html')

# --- Servir archivos estáticos (¡MODIFICADO!) ---
@app.route('/static/<path:filename>')
def serve_static(filename):
    # Esta ruta ahora sirve CUALQUIER COSA dentro de la carpeta 'static'
    # Incluyendo la nueva carpeta 'uploads_persistent'
    return send_from_directory(STATIC_DIR, filename)

# --- Iniciar Servidor ---
if __name__ == '__main__':
    # Asegurarse de que las carpetas persistentes existan al iniciar
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
    app.run(debug=True, port=5000)