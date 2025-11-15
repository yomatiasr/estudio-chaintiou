import streamlit as st
import sqlite3
import hashlib
import json
import os
from datetime import datetime

# --- CONFIG ---
DB_PATH = "Estudio_Chaintiou.db"
USUARIOS_FILE = "usuarios.json"

# --- INICIALIZAR ARCHIVOS ---
if not os.path.exists(USUARIOS_FILE):
    default = {u: hashlib.md5("1234".encode()).hexdigest() for u in ["admin", "ariel", "fiorella", "daiana", "matias"]}
    json.dump(default, open(USUARIOS_FILE, "w"), indent=4)

if not os.path.exists(DB_PATH):
    st.error("Base de datos no encontrada. Ejecuta la app de escritorio primero.")
    st.stop()

# --- CONEXIÓN DB ---
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- LOGIN ---
if 'logged' not in st.session_state:
    st.session_state.logged = False
    st.session_state.user = ""

if not st.session_state.logged:
    st.title("Estudio Chaintiou - Login")
    user = st.text_input("Usuario", value="admin")
    pwd = st.text_input("Contraseña", type="password", value="1234")
    if st.button("Entrar"):
        usuarios = json.load(open(USUARIOS_FILE))
        if user in usuarios and usuarios[user] == hashlib.md5(pwd.encode()).hexdigest():
            st.session_state.logged = True
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Credenciales incorrectas")
    st.stop()

# --- LOGOUT ---
if st.sidebar.button("Cerrar sesión"):
    st.session_state.logged = False
    st.session_state.user = ""
    st.rerun()

st.sidebar.success(f"**{st.session_state.user.upper()}**")

# --- PESTAÑAS ---
tab1, tab2, tab3, tab4 = st.tabs(["Clientes", "Facturas", "Pagos", "Impuestos"])

# --- FUNCIÓN VALIDAR CUIT ---
def validar_cuit(cuit):
    cuit = ''.join(filter(str.isdigit, str(cuit)))
    if len(cuit) != 11: return False
    m = [5,4,3,2,7,6,5,4,3,2]
    s = sum(int(cuit[i])*m[i] for i in range(10))
    v = 11 - s%11 if s%11 != 0 else 0
    return v == int(cuit[10])

# ================== CLIENTES ==================
with tab1:
    st.header("Gestión de Clientes")
    
    with st.expander("Agregar / Modificar Cliente", expanded=True):
        with st.form("form_cliente"):
            col1, col2 = st.columns(2)
            nombre = col1.text_input("Nombre")
            apellido = col2.text_input("Apellido")
            cuit = col1.text_input("CUIT")
            domicilio = col2.text_input("Domicilio")
            telefono = col1.text_input("Teléfono")
            email = col2.text_input("Email")
            cliente_id = st.text_input("ID (para modificar)", disabled=True)
            submit = st.form_submit_button("Guardar")
            
            if submit:
                if not validar_cuit(cuit):
                    st.error("CUIT inválido")
                else:
                    with get_conn() as conn:
                        cur = conn.cursor()
                        if cliente_id:
                            cur.execute("""UPDATE clientes SET nombre=?, apellido=?, cuit=?, domicilio=?, telefono=?, email=?
                                           WHERE id_cliente=?""", (nombre, apellido, cuit, domicilio, telefono, email, cliente_id))
                        else:
                            cur.execute("SELECT * FROM clientes WHERE cuit=?", (cuit,))
                            if cur.fetchone():
                                st.error("CUIT ya existe")
                            else:
                                cur.execute("""INSERT INTO clientes (nombre, apellido, cuit, domicilio, telefono, email)
                                               VALUES (?, ?, ?, ?, ?, ?)""", (nombre, apellido, cuit, domicilio, telefono, email))
                        conn.commit()
                        st.success("Cliente guardado")
                        st.rerun()

    # --- BUSCAR ---
    st.subheader("Buscar Cliente")
    col1, col2 = st.columns([1, 3])
    tipo_busqueda = col1.selectbox("Buscar por", ["CUIT", "Apellido", "ID"])
    valor = col2.text_input("Valor")
    if st.button("Buscar"):
        with get_conn() as conn:
            cur = conn.cursor()
            if tipo_busqueda == "CUIT":
                cur.execute("SELECT * FROM clientes WHERE cuit=?", (valor,))
            elif tipo_busqueda == "Apellido":
                cur.execute("SELECT * FROM clientes WHERE apellido=?", (valor,))
            else:
                cur.execute("SELECT * FROM clientes WHERE id_cliente=?", (valor,))
            r = cur.fetchone()
            if r:
                st.session_state.cliente_edit = dict(r)
                st.rerun()
            else:
                st.error("No encontrado")

    if 'cliente_edit' in st.session_state:
        c = st.session_state.cliente_edit
        st.info(f"Editando: {c['nombre']} {c['apellido']} (ID: {c['id_cliente']})")
        # Aquí puedes rellenar el form con st.experimental_rerun()

    # --- TABLA ---
    with get_conn() as conn:
        clientes = conn.execute("SELECT * FROM clientes").fetchall()
        if clientes:
            data = [dict(row) for row in clientes]
            st.dataframe(data, use_container_width=True)
        else:
            st.info("No hay clientes")

# ================== FACTURAS ==================
with tab2:
    st.header("Facturas")
    # Similar a clientes...
    st.write("Próximamente: agregar, modificar, buscar facturas")

# ================== PAGOS ==================
with tab3:
    st.header("Pagos")
    st.write("Próximamente: registrar pagos")

# ================== IMPUESTOS ==================
with tab4:
    st.header("Impuestos")
    st.write("Próximamente: gestionar impuestos")

st.sidebar.info("Sistema Contable - Versión Web")
