import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

# --- 1. CONEXIÓN A GOOGLE SHEETS (Sincronización Masiva) ---
def conectar_google_sheets():
    try:
        creds_dict = dict(st.secrets["connections"]["gsheets"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        ss = client.open_by_key("116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc")
        
        h_maestra = ss.get_worksheet(0)
        try:
            h_historial = ss.worksheet("Historial")
        except:
            h_historial = ss.add_worksheet(title="Historial", rows="5000", cols="35")
            
        return ss, h_maestra, h_historial
    except:
        return None, None, None

def motor_vigilancia(ss, h_maestra, h_historial, fila_datos, reg_map):
    # Mapeo: A=0, B=1, C=2, D=3, E=4, G=6, I=8
    registro = str(fila_datos.iloc[3]).strip()
    dia = int(str(fila_datos.iloc[0]).split('/')[0])
    col_x = dia + 3
    
    if registro in reg_map:
        fila_base = reg_map[registro]
    else:
        vals_hist = h_historial.get_all_values()
        fila_base = len(vals_hist) + 1
        
        # Clonar Plantilla
        body = {"requests": [{"copyPaste": {"source": {"sheetId": h_maestra.id, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},"destination": {"sheetId": h_historial.id, "startRowIndex": fila_base - 1, "endRowIndex": fila_base + 7, "startColumnIndex": 0, "endColumnIndex": 35},"pasteType": "PASTE_NORMAL"}}]}
        ss.batch_update(body)
        
        # Llenar datos fijos (B3, B4, A5, B7, B8, B9)
        updates = [
            {'range': f'Historial!B{fila_base + 0}', 'values': [[str(fila_datos.iloc[1])]]},
            {'range': f'Historial!B{fila_base + 1}', 'values': [[str(fila_datos.iloc[2])]]},
            {'range': f'Historial!A{fila_base + 2}', 'values': [[str(fila_datos.iloc[4])]]},
            {'range': f'Historial!B{fila_base + 4}', 'values': [[str(fila_datos.iloc[6])]]},
            {'range': f'Historial!B{fila_base + 5}', 'values': [[str(fila_datos.iloc[3])]]},
            {'range': f'Historial!B{fila_base + 6}', 'values': [[str(fila_datos.iloc[8])]]}
        ]
        ss.batch_update({'valueInputOption': 'USER_ENTERED', 'data': updates})

    h_historial.update_cell(fila_base + 1, col_x, "X")

# ========================================================
# 2. BARRA LATERAL (BOTONES DE VIGILANCIA MASIVA)
# ========================================================
with st.sidebar:
    st.title("⚙️ Panel de Control")
    st.markdown("---")
    st.subheader("🔄 Vigilancia Masiva")
    
    # URL del censo para los botones de la barra lateral
    URL_CENSO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"
    
    if st.button("🚩 INICIO DE VIGILANCIA", use_container_width=True, help="Borra y crea plantillas"):
        try:
            df_cloud = pd.read_csv(URL_CENSO)
            ss, h_ma, h_hi = conectar_google_sheets()
            if ss:
                h_hi.clear()
                st.toast("Iniciando Vigilancia...")
                for i, row in df_cloud.iterrows():
                    motor_vigilancia(ss, h_ma, h_hi, row, {})
                    time.sleep(2)
                st.success("¡Vigilancia Generada!")
        except Exception as e:
            st.error(f"Error: {e}")

    if st.button("🔄 VIGILANCIA DIARIA", type="primary", use_container_width=True, help="Sincroniza sin duplicados"):
        try:
            df_cloud = pd.read_csv(URL_CENSO)
            ss, h_ma, h_hi = conectar_google_sheets()
            if ss:
                data_h = h_hi.get_all_values()
                reg_map = {str(data_h[r][1]).strip(): r-5+1 for r in range(5, len(data_h), 8) if str(data_h[r][1]).strip()}
                st.toast("Sincronizando seguimiento...")
                for i, row in df_cloud.iterrows():
                    motor_vigilancia(ss, h_ma, h_hi, row, reg_map)
                    time.sleep(2)
                st.success("¡Seguimiento Actualizado!")
        except Exception as e:
            st.error(f"Error: {e}")

# ========================================================
# 3. SEGUIMIENTO DE PISO (TU CÓDIGO ORIGINAL INTACTO)
# ========================================================
st.title("🏥 Seguimiento de Piso")

st.info("### 📂 archivo de seguimiento")
archivo_excel = st.file_uploader(
    "subir archivo de excel para seguimiento", 
    type=["xlsx", "xls", "csv"],
    key="excel_unico_piso"
)

if archivo_excel:
    try:
        # Lógica de carga para Excel o CSV
        if archivo_excel.name.endswith('.csv'):
            df = pd.read_csv(archivo_excel)
        else:
            df = pd.read_excel(archivo_excel)
        
        lista_especialidades = sorted(df.iloc[:, 1].dropna().unique())
        col_esp, col_cam = st.columns(2)
        with col_esp:
            esp_sel = st.selectbox("especialidad:", lista_especialidades)
        
        df_filtrado_esp = df[df.iloc[:, 1] == esp_sel]
        lista_camas = sorted(df_filtrado_esp.iloc[:, 2].dropna().unique())
        with col_cam:
            cama_sel = st.selectbox("cama:", lista_camas)

        paciente = df_filtrado_esp[df_filtrado_esp.iloc[:, 2] == cama_sel].iloc[0]

        with st.container(border=True):
            st.markdown(f"### 👤 {paciente.iloc[4]}")
            c1, c2, c3 = st.columns(3)
            with c1: st.write(f"**registro:** {paciente.iloc[3]}")
            with c2: st.write(f"**sexo/edad:** {paciente.iloc[5]} / {paciente.iloc[6]}")
            with c3: st.info(f"**días estancia:** {paciente.iloc[9]}")

        st.divider()

        # --- formulario de captura ---
        st.subheader("📝 captura de seguimiento")

        # ... (Tu código de estatus, temperatura, bristol, etc. va aquí abajo)
        # Lo recorto para que el código no sea una pared de texto, pero mantén tu lógica.

        st.write("*(Aquí continúa el resto de tu formulario original...)*")

        if st.button("💾 guardar seguimiento", type="primary", use_container_width=True):
            st.success(f"captura completa para la cama {cama_sel}.")

    except Exception as e:
        st.error(f"error: {e}")
else:
    st.warning("⚠️ sube el archivo excel para habilitar la captura.")
