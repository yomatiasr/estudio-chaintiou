import streamlit as st
import sqlite3
import hashlib
import json
import os
import requests

# --- CONFIG ---
DB_PATH = "Estudio_Chaintiou.db"
USUARIOS_FILE = "usuarios.json"
DRIVE_ID = "1EGNLpJ3czGCd83b6i4IJxazi3PdWxvnB"  # TU ID

# --- DESCARGAR DB ---
@st.cache_resource
def descargar_db():
    if not os.path.exists(DB_PATH):
        st.info("Descargando base de datos desde Google Drive...")
        url = f"https://drive.google.com/uc?export=download&id={DRIVE_ID}"
        try:
            r = requests.get(url, stream=True)
            r.raise_for_status()
            with open(DB_PATH, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            st.success("Base de datos descargada")
        except Exception as e:
            st.error(f"Error al descargar: {e}")
            st.stop()
    return DB_PATH

# --- INICIALIZAR ---
if not os.path.exists(USUARIOS_FILE):
    default = {u: hashlib.md5("1234".encode()).hexdigest() for u in ["admin", "ariel", "fiorella", "daiana", "matias"]}
    json.dump(default, open(USUARIOS_FILE, "w"), indent=4)

descargar_db()

# --- CONEXIÓN DB ---
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ========================= LOGIN & CAMBIO DE CONTRASEÑA =========================
if 'logged' not in st.session_state:
    st.session_state.logged = False
    st.session_state.user = ""

# ---- CAMBIO DE CONTRASEÑA ----
if st.session_state.logged:
    with st.sidebar.expander("Cambiar contraseña", expanded=False):
        nueva = st.text_input("Nueva contraseña", type="password", key="nueva")
        repetir = st.text_input("Repetir contraseña", type="password", key="repetir")
        if st.button("Actualizar contraseña"):
            if nueva == repetir and len(nueva) >= 4:
                usuarios = json.load(open(USUARIOS_FILE))
                usuarios[st.session_state.user] = hashlib.md5(nueva.encode()).hexdigest()
                json.dump(usuarios, open(USUARIOS_FILE, "w"), indent=4)
                st.success("¡Contraseña actualizada!")
                st.rerun()
            else:
                st.error("Las contraseñas no coinciden o son muy cortas")

    if st.sidebar.button("Cerrar sesión"):
        st.session_state.logged = False
        st.session_state.user = ""
        st.rerun()

# ---- LOGIN ----
if not st.session_state.logged:
    st.title("Estudio Chaintiou - Sistema Contable")
    col1, col2 = st.columns([1, 1])
    with col1:
        st.image("https://i.imgur.com/5zq2R0J.png", width=200)  # opcional logo
    with col2:
        user = st.text_input("Usuario", value="admin")
        pwd = st.text_input("Contraseña", type="password", value="1234")
        if st.button("INGRESAR", type="primary", use_container_width=True):
            usuarios = json.load(open(USUARIOS_FILE))
            if user in usuarios and usuarios[user] == hashlib.md5(pwd.encode()).hexdigest():
                st.session_state.logged = True
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
    st.stop()

st.sidebar.success(f"**{st.session_state.user.upper()}**")

# ========================= TEMAS =========================
temas = {
    "Claro (predeterminado)": "light",
    "Oscuro": "dark",
    "Azul": "blue",
    "Verde": "green",
    "Violeta": "purple",
    "Naranja": "orange"
}

tema_elegido = st.sidebar.selectbox("Tema", options=list(temas.keys()), index=0)
st.set_page_config(page_title="Estudio Chaintiou", layout="wide")
if temas[tema_elegido] != "light":
    st.markdown(f'<style>body {{background-color: var(--background-color-{temas[tema_elegido]});}}</style>', unsafe_allow_html=True)

# --- VALIDAR CUIT ---
def validar_cuit(cuit):
    cuit = ''.join(filter(str.isdigit, str(cuit)))
    if len(cuit) != 11: return False
    m = [5,4,3,2,7,6,5,4,3,2]
    s = sum(int(cuit[i])*m[i] for i in range(10))
    v = 11 - s%11 if s%11 != 0 else 0
    return v == int(cuit[10])

# --- PESTAÑAS ---
tab1, tab2, tab3, tab4 = st.tabs(["Clientes", "Facturas", "Pagos", "Impuestos"])

# ================== CLIENTES ==================
with tab1:
    st.header("Gestión de Clientes")
    
    with st.expander("Agregar / Modificar Cliente", expanded=True):
        with st.form("form_cliente"):
            col1, col2 = st.columns(2)
            nombre = col1.text_input("Nombre")
            apellido = col1.text_input("Apellido")
            cuit = col1.text_input("CUIT")
            domicilio = col2.text_input("Domicilio")
            telefono = col2.text_input("Teléfono")
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
    tipo_busqueda = col1.selectbox("Buscar por", ["CUIT", "Apellido", "ID"], key="busq_cli")
    valor = col2.text_input("Valor", key="val_cli")
    if st.button("Buscar", key="btn_cli"):
        with get_conn() as conn:
            cur = conn.cursor()
            if tipo_busqueda == "CUIT":
                cur.execute("SELECT * FROM clientes WHERE cuit=?", (valor,))
            elif tipo_busqueda == "Apellido":
                cur.execute("SELECT * FROM clientes WHERE apellido LIKE ?", (f"%{valor}%",))
            else:
                cur.execute("SELECT * FROM clientes WHERE id_cliente=?", (valor,))
            r = cur.fetchone()
            if r:
                st.session_state.edit_cliente = dict(r)
                st.rerun()
            else:
                st.error("No encontrado")

    if 'edit_cliente' in st.session_state:
        c = st.session_state.edit_cliente
        st.info(f"Editando: {c['nombre']} {c['apellido']} (ID: {c['id_cliente']})")
        # Puedes rellenar el form con st.rerun()

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
    
    with st.expander("Agregar / Modificar Factura", expanded=True):
        with st.form("form_factura"):
            col1, col2 = st.columns(2)
            id_cliente = col1.number_input("ID Cliente", min_value=1)
            fecha_emision = col2.date_input("Fecha Emisión")
            monto_total = col1.number_input("Monto Total", min_value=0.0, format="%.2f")
            descripcion = col2.text_area("Descripción")
            estado = col1.selectbox("Estado", ["Pendiente", "Pagada", "Vencida"])
            fecha_vencimiento = col2.date_input("Fecha Vencimiento")
            factura_id = st.text_input("ID (para modificar)", disabled=True)
            submit = st.form_submit_button("Guardar")
            
            if submit:
                with get_conn() as conn:
                    cur = conn.cursor()
                    if factura_id:
                        cur.execute("""UPDATE facturas SET id_cliente=?, fecha_emision=?, monto_total=?, descripcion=?, estado=?, fecha_vencimiento=?
                                       WHERE id_factura=?""", (id_cliente, fecha_emision, monto_total, descripcion, estado, fecha_vencimiento, factura_id))
                    else:
                        cur.execute("""INSERT INTO facturas (id_cliente, fecha_emision, monto_total, descripcion, estado, fecha_vencimiento)
                                       VALUES (?, ?, ?, ?, ?, ?)""", (id_cliente, fecha_emision, monto_total, descripcion, estado, fecha_vencimiento))
                    conn.commit()
                    st.success("Factura guardada")
                    st.rerun()

    # --- BUSCAR ---
    st.subheader("Buscar Factura")
    id_busq = st.text_input("ID Factura")
    if st.button("Buscar Factura"):
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM facturas WHERE id_factura=?", (id_busq,))
            r = cur.fetchone()
            if r:
                st.session_state.edit_factura = dict(r)
                st.rerun()
            else:
                st.error("No encontrada")

    # --- TABLA ---
    with get_conn() as conn:
        facturas = conn.execute("SELECT * FROM facturas").fetchall()
        if facturas:
            data = [dict(row) for row in facturas]
            st.dataframe(data, use_container_width=True)
        else:
            st.info("No hay facturas")

# ================== PAGOS ==================
with tab3:
    st.header("Pagos")
    
    with st.expander("Agregar / Modificar Pago", expanded=True):
        with st.form("form_pago"):
            col1, col2 = st.columns(2)
            id_factura = col1.number_input("ID Factura", min_value=1)
            fecha_pago = col2.date_input("Fecha Pago")
            metodo_pago = col1.selectbox("Método", ["Efectivo", "Transferencia", "Tarjeta", "Cheque"])
            nota = col2.text_area("Nota")
            pago_id = st.text_input("ID (para modificar)", disabled=True)
            submit = st.form_submit_button("Guardar")
            
            if submit:
                with get_conn() as conn:
                    cur = conn.cursor()
                    if pago_id:
                        cur.execute("""UPDATE pagos SET id_factura=?, fecha_pago=?, metodo_pago=?, nota=?
                                       WHERE id_pago=?""", (id_factura, fecha_pago, metodo_pago, nota, pago_id))
                    else:
                        cur.execute("""INSERT INTO pagos (id_factura, fecha_pago, metodo_pago, nota)
                                       VALUES (?, ?, ?, ?)""", (id_factura, fecha_pago, metodo_pago, nota))
                    conn.commit()
                    st.success("Pago guardado")
                    st.rerun()

    # --- TABLA ---
    with get_conn() as conn:
        pagos = conn.execute("SELECT * FROM pagos").fetchall()
        if pagos:
            data = [dict(row) for row in pagos]
            st.dataframe(data, use_container_width=True)
        else:
            st.info("No hay pagos")

# ================== IMPUESTOS ==================
with tab4:
    st.header("Impuestos")
    
    with st.expander("Agregar / Modificar Impuesto", expanded=True):
        with st.form("form_impuesto"):
            col1, col2 = st.columns(2)
            id_cliente = col1.number_input("ID Cliente", min_value=1)
            tipo = col2.text_input("Tipo")
            fecha_a_pagar = col1.date_input("Fecha a Pagar")
            monto = col2.number_input("Monto", min_value=0.0, format="%.2f")
            impuesto_id = st.text_input("ID (para modificar)", disabled=True)
            submit = st.form_submit_button("Guardar")
            
            if submit:
                with get_conn() as conn:
                    cur = conn.cursor()
                    if impuesto_id:
                        cur.execute("""UPDATE impuestos SET id_cliente=?, tipo=?, fecha_a_pagar=?, monto=?
                                       WHERE id_impuesto=?""", (id_cliente, tipo, fecha_a_pagar, monto, impuesto_id))
                    else:
                        cur.execute("""INSERT INTO impuestos (id_cliente, tipo, fecha_a_pagar, monto)
                                       VALUES (?, ?, ?, ?)""", (id_cliente, tipo, fecha_a_pagar, monto))
                    conn.commit()
                    st.success("Impuesto guardado")
                    st.rerun()

    # --- TABLA ---
    with get_conn() as conn:
        impuestos = conn.execute("SELECT * FROM impuestos").fetchall()
        if impuestos:
            data = [dict(row) for row in impuestos]
            st.dataframe(data, use_container_width=True)
        else:
            st.info("No hay impuestos")

st.sidebar.info("Sistema Contable Completo - Web en la Nube")
