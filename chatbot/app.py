#===========================================================================================================#
#  *****     Este codigo se deasarrollo con la ayuda de mis mejores amigos GTP y Copilot <3        *****    #
#  *****     Si no le sabes no le muevas porfi                                                     *****    #
#  *****     si fucnciona correctamente no le muevas x2                                            *****    #
#  *****     Como extraño a esa cabrona , Regresa valeria diria el emi XD                          *****    #
#  *****     Bueno si la ven diganle que la amo y que todas las noches la extraño                  *****    #
#  *****     bueno ya                                                                              *****    #
#  *****     con respecto al codigo , para ejecutarlo activen el .env y despues                    *****    #
#  *****     intsalen las dependencias de requirements.txt                                         *****    #
#  *****     cya despues de que se instalen entras a la carpeta con                                *****    #
#  *****     cd chatbot y despues pyhton app.py                                                    *****    #
#  *****     y ya... hasta ahora.                                                                  *****    #
#===========================================================================================================#

# ===============================================
# DEPENDENCIAS
# ===============================================
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import psycopg2
import psycopg2.extras
import bcrypt
import datetime
from functools import wraps
from openai import OpenAI
from flask_cors import CORS

# ===============================================
# CONFIGURACIÓN FLASK
# ===============================================
app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)  # Permitir peticiones del ESP32
# ===============================================
# CONFIGURACIÓN OPENAI
# ===============================================
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
def obtener_respuesta(pregunta):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un asistente interno para empleados."},
                {"role": "user", "content": pregunta}
            ],
            max_tokens=512,
        )
        if response and response.choices:
            return response.choices[0].message.content.strip() or "Sin respuesta del modelo."
        return "No se obtuvo respuesta válida del modelo."
    except Exception as e:
        print("Error al conectar con OpenAI:", repr(e))
        return "No se pudo obtener respuesta. Error de conexión con el servicio de IA."

# ===============================================
# CONFIGURACIÓN BASE DE DATOS
# ===============================================
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "usuarios_geston"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "gestonebm"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}

def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.cursor_factory = psycopg2.extras.DictCursor
    return conn

# ===============================================
# DECORADORES Y FUNCIONES DE SESIÓN
# ===============================================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Debes iniciar sesión para enviar mensajes"}), 401
        return f(*args, **kwargs)
    return decorated

def require_area(area):
    if not session.get("loggedin") or session.get("area") != area:
        return redirect(url_for("login"))
    return None

# ===============================================
# LOGIN
# ===============================================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return render_template("login.html", error="Debes llenar todos los campos")

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("SELECT * FROM usuarios WHERE username = %s", (username,))
            user = cur.fetchone()
            cur.close()
            conn.close()

            if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                
                session["loggedin"] = True
                session["user_id"] = user['id']
                session["username"] = user['username']
                session["area"] = user['area']
                session["nivel"] = user['nivel']

            
                if user['area'] == "finanzas":
                    return redirect(url_for("chatbot_finanzas"))
                elif user['area'] == "ventas":
                    return redirect(url_for("chatbot_ventas"))
                elif user['area'] == "admin":
                    return redirect(url_for("chatbot_admin"))
                else:
                    return redirect(url_for("login"))

            return render_template("login.html", error="Usuario o contraseña incorrectos")
        except Exception as e:
            print("Error login:", e)
            return render_template("login.html", error=f"Error en la base de datos: {str(e)}")
    return render_template("login.html")
# ===============================================
# REGISTRO DE USUARIOS
# ===============================================
@app.route("/register", methods=["GET", "POST"])
@login_required   
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        area = request.form.get("area")
        nivel = request.form.get("nivel", "1")  

       
        if not username or not password or not area or not nivel:
            return render_template("register.html", error="Debes llenar todos los campos")

        
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO usuarios (username, password, area, nivel)
                VALUES (%s, %s, %s, %s)
            """, (username, hashed, area, nivel))
            conn.commit()
            cur.close()
            conn.close()

            return redirect(url_for("chatbot_admin"))  

        except Exception as e:
            print("Error al registrar usuario:", e)
            return render_template("register.html", error="Ese usuario ya existe o hubo un error en la BD.")

    return render_template("register.html")


# ===============================================
# CHAT
# ===============================================
@app.route("/chat", methods=["POST"])
@login_required
def chat():
    data = request.get_json()
    mensaje_usuario = data.get("mensaje")
    if not mensaje_usuario:
        return jsonify({"error": "Mensaje vacío"}), 400

    user_id = session["user_id"]
    conn = get_db_connection()
    cur = conn.cursor()


    id_historial = session.get("id_historial")
    if not id_historial:
        cur.execute("SELECT id FROM historial WHERE user_id=%s ORDER BY fecha DESC LIMIT 1", (user_id,))
        fila = cur.fetchone()
        if fila:
            id_historial = fila[0]
        else:
            cur.execute("INSERT INTO historial (titulo, user_id) VALUES (%s,%s) RETURNING id",
                        ("Nueva conversación", user_id))
            id_historial = cur.fetchone()[0]
        session["id_historial"] = id_historial

    
    cur.execute("""
        SELECT remitente, texto FROM mensajes 
        WHERE id_historial=%s ORDER BY id ASC
    """, (id_historial,))
    historial = cur.fetchall()

    messages = [{"role": "system", "content": "Eres un asistente interno para empleados."}]
    for remitente, texto in historial:
        if remitente == "user":
            messages.append({"role": "user", "content": texto})
        else:
            messages.append({"role": "assistant", "content": texto})

    messages.append({"role": "user", "content": mensaje_usuario})


    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=512,
        )
        respuesta = response.choices[0].message.content.strip()
    except Exception as e:
        print("Error IA:", e)
        respuesta = "Hubo un error con el modelo."


    cur.execute("INSERT INTO mensajes (id_historial, remitente, texto) VALUES (%s,%s,%s)",
                (id_historial, "user", mensaje_usuario))
    cur.execute("INSERT INTO mensajes (id_historial, remitente, texto) VALUES (%s,%s,%s)",
                (id_historial, "bot", respuesta))


    cur.execute("UPDATE historial SET titulo=%s WHERE id=%s AND titulo='Nueva conversación'",
                (respuesta[:30] + "...", id_historial))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"respuesta": respuesta})



@app.route("/historial_titulos", methods=["GET"])
@login_required
def historial_titulos():
    user_id = session["user_id"]
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, titulo, fecha FROM historial WHERE user_id=%s ORDER BY fecha DESC", (user_id,))
    filas = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([{"id": f[0], "titulo": f[1], "fecha": f[2].strftime("%d/%m/%Y %H:%M")} for f in filas])



@app.route("/historial_detalle/<int:id_historial>", methods=["GET"])
@login_required
def historial_detalle(id_historial):
    conn = get_db_connection()
    cur = conn.cursor()


    cur.execute("SELECT id FROM historial WHERE id=%s", (id_historial,))
    if cur.fetchone() is None:
        cur.close()
        conn.close()
        return jsonify([])

    cur.execute("""
        SELECT remitente, texto, fecha
        FROM mensajes
        WHERE id_historial=%s
        ORDER BY fecha ASC
    """, (id_historial,))
    data = cur.fetchall()

    cur.close()
    conn.close()

    mensajes = []
    for remitente, texto, fecha in data:
        mensajes.append({
            "remitente": "usuario" if remitente.lower() == "user" else "bot",
            "texto": texto,
            "fecha": fecha.strftime("%H:%M")
        })

    return jsonify(mensajes)



@app.route("/nuevo_chat", methods=["POST"])
@login_required
def nuevo_chat():
    user_id = session["user_id"]
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO historial (titulo, user_id) VALUES (%s,%s) RETURNING id",
                ("Nueva conversación", user_id))
    id_historial = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    session["id_historial"] = id_historial
    return jsonify({"id_historial": id_historial})


@app.route("/eliminar_historial/<int:id_historial>", methods=["DELETE"])
@login_required
def eliminar_historial(id_historial):
    user_id = session["user_id"]
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM historial WHERE id=%s AND user_id=%s", (id_historial, user_id))
    conn.commit()

    cur.close()
    conn.close()
    return "", 204


# ===============================================
# CHATBOT POR ÁREA
# ===============================================
@app.route("/chatbot_admin")
@login_required
def chatbot_admin():
    redirection = require_area("admin")
    if redirection: return redirection
    return render_template("index.html", username=session.get("username"))

@app.route("/chatbot_finanzas")
@login_required
def chatbot_finanzas():
    redirection = require_area("finanzas")
    if redirection: return redirection
    return render_template("finanzas.html", username=session.get("username"))


@app.route("/chatbot_ventas")
@login_required
def chatbot_ventas():
    redirection = require_area("ventas")
    if redirection: return redirection
    return render_template("ventas.html", username=session.get("username"))

# ===============================================
# ADMIN PANEL Y EDICIÓN DE USUARIOS
# ===============================================
@app.route("/admin_panel")
def admin_panel():
    redirection = require_area("admin")
    if redirection: return redirection

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM usuarios")
        usuarios = cur.fetchall()
        cur.close()
        conn.close()
        usuarios_activos = sum(1 for u in usuarios if u['area'] != 'inactivo')
        return render_template("admin_panel.html", usuarios=usuarios, usuarios_activos=usuarios_activos)
    except Exception as e:
        print("Error al cargar panel:", e)
        return render_template("admin_panel.html", usuarios=[], usuarios_activos=0)

@app.route("/edit", methods=["GET"])
def edit():
    redirection = require_area("admin")
    if redirection: return redirection

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT DISTINCT area FROM usuarios ORDER BY area")
        areas = [r["area"] for r in cur.fetchall()]

        selected_area = request.args.get("area")
        usuarios = []
        if selected_area:
            cur.execute("SELECT * FROM usuarios WHERE area=%s ORDER BY username", (selected_area,))
            usuarios = cur.fetchall()

        cur.close()
        conn.close()
        return render_template("edit.html", areas=areas, usuarios=usuarios, selected_area=selected_area)
    except Exception as e:
        print("Error edit:", e)
        return "Error interno del servidor", 500

@app.route("/actualizar_usuario/<int:user_id>", methods=["POST"])
def actualizar_usuario(user_id):
    redirection = require_area("admin")
    if redirection: return redirection

    password = request.form.get("password")
    nivel = request.form.get("nivel")
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        if password:
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cur.execute("UPDATE usuarios SET nivel=%s, password=%s WHERE id=%s", (nivel, hashed, user_id))
        else:
            cur.execute("UPDATE usuarios SET nivel=%s WHERE id=%s", (nivel, user_id))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("edit", area=request.args.get("area")))
    except Exception as e:
        print("Error actualizar usuario:", e)
        return "Error interno del servidor", 500

@app.route("/eliminar_usuario/<int:user_id>")
def eliminar_usuario(user_id):
    redirection = require_area("admin")
    if redirection: return redirection

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM usuarios WHERE id=%s", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("edit", area=request.args.get("area")))
    except Exception as e:
        print("Error eliminar usuario:", e)
        return "Error interno del servidor", 500

# ===============================================
# LOGS
# ===============================================
def agregar_log(user_id, accion, descripcion, ip_usuario):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO logs (user_id, accion, descripcion, ip_usuario, fecha)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, accion, descripcion, ip_usuario, datetime.datetime.now()))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Error al insertar log:", e)

@app.route("/logs")
def ver_logs():
    redirection = require_area("admin")
    if redirection: return redirection
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM logs ORDER BY fecha DESC")
        logs = cur.fetchall()
        cur.close()
        conn.close()
        return render_template("logs.html", logs=logs)
    except Exception as e:
        print("Error al cargar logs:", e)
        return f"Error al cargar logs: {e}"

# ===============================================
# API PARA ESP32 - AUTENTICACIÓN POR HUELLA
# ===============================================
@app.route('/api/fingerprint/status', methods=['GET'])
def fingerprint_status():
    """
    Endpoint para verificar que el servicio está funcionando.
    El ESP32 puede usar esto para hacer un "ping" inicial.
    """
    return jsonify({
        'status': 'online',
        'service': 'fingerprint-auth-gestion-ebm',
        'version': '1.0',
        'message': 'Sistema de autenticación por huella activo'
    })


@app.route('/api/fingerprint/verify', methods=['POST'])
def fingerprint_verify():
    """
    Verifica si una huella existe en el sistema (sin hacer login).
    
    Espera JSON: {"sensor_id": 123}
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No se recibió JSON'
            }), 400
        
        sensor_id = data.get('sensor_id')
        
        if sensor_id is None:
            return jsonify({
                'success': False,
                'error': 'sensor_id es requerido'
            }), 400
        
        # Buscar huella en la tabla huellas y obtener el usuario
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT u.*, h.finger_id 
            FROM huellas h
            JOIN usuarios u ON h.user_id = u.id
            WHERE h.finger_id = %s
        """, (sensor_id,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user:
            return jsonify({
                'success': True,
                'exists': True,
                'sensor_id': sensor_id,
                'username': user['username'],
                'area': user['area'],
                'nivel': user['nivel']
            })
        else:
            return jsonify({
                'success': True,
                'exists': False,
                'sensor_id': sensor_id,
                'message': 'Huella no registrada'
            })
        
    except Exception as e:
        print(f"Error en fingerprint_verify: {e}")
        return jsonify({
            'success': False,
            'error': f'Error interno: {str(e)}'
        }), 500


@app.route('/api/fingerprint/login', methods=['POST'])
def fingerprint_login():
    """
    Endpoint para autenticación por huella desde ESP32.
    
    Espera JSON: 
    {
        "sensor_id": 123,
        "device_id": "ESP32_001"  (opcional)
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No se recibió JSON'
            }), 400
        
        sensor_id = data.get('sensor_id')
        device_id = data.get('device_id', 'unknown')
        
        if sensor_id is None:
            return jsonify({
                'success': False,
                'error': 'sensor_id es requerido'
            }), 400
        
        # Buscar usuario por finger_id en la tabla huellas
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT u.*, h.finger_id 
            FROM huellas h
            JOIN usuarios u ON h.user_id = u.id
            WHERE h.finger_id = %s
        """, (sensor_id,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user:
            # Usuario encontrado - registrar en logs
            ip_usuario = request.remote_addr
            agregar_log(user['id'], 'Login por huella', 
                       f'Finger ID: {sensor_id}, Device: {device_id}', 
                       ip_usuario)
            
            print(f"✅ Login por huella exitoso - Usuario: {user['username']}, "
                  f"Finger ID: {sensor_id}, Device: {device_id}, Área: {user['area']}")
            
            return jsonify({
                'success': True,
                'message': 'Autenticación exitosa',
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'area': user['area'],
                    'nivel': user['nivel']
                },
                'redirect': f"/chatbot_{user['area']}"  # Para redirección futura
            })
        else:
            # Huella no registrada
            print(f"❌ Huella no registrada - Finger ID: {sensor_id}")
            return jsonify({
                'success': False,
                'error': 'Huella no registrada en el sistema',
                'sensor_id': sensor_id
            }), 404
            
    except Exception as e:
        print(f"⚠️ Error en fingerprint_login: {e}")
        return jsonify({
            'success': False,
            'error': f'Error interno: {str(e)}'
        }), 500
# ===============================================
# EJECUTAR LA APP
# ===============================================
if __name__ == "__main__":
    app.run(debug=True)
