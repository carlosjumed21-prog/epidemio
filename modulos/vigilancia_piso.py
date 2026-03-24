import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import time

# --- 1. CONEXIÓN ---
def conectar_piso_activo():
    try:
        creds_dict = dict(st.secrets["connections"]["gsheets"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # Origen: Datos Limpios
        ss_origen = client.open_by_key("1yKgI1CxWGxIFSRNaG8WoTTmZ__mEkkfhNqcL-2T_ePM")
        # Salida: Vigilancia Activa de Piso
        ss_salida = client.open_by_key("1GWFWY1PyfUERC9S0QYvOsugpvrIPQiRS7vyCval9ZTc")
        
        h_datos_limpios = ss_origen.get_worksheet(1) # Hoja 2 del origen
        h_plantilla = ss_salida.get_worksheet(0)     # Hoja 1 (Plantilla)
        h_seguimiento = ss_salida.get_worksheet(1)   # Hoja 2 (Destino/Seguimiento)
            
        return ss_salida, h_plantilla, h_datos_limpios, h_seguimiento
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None, None, None, None

# --- 2. FUNCIÓN DE MAPEO (BLOQUE 10 FILAS) ---
def actualizar_bloque_piso(h_sheet, fila_base, fila_datos):
    try:
        # Extraer día para la "X"
        fecha_str = str(fila_datos.iloc[0])
        dia = int(fecha_str.split('/')[0])
        col_dia = dia + 2  # Día 1 en Col C(3)

        lista_celdas = [
            gspread.Cell(row=fila_base + 2, col=2, value=str(fila_datos.iloc[4])),  # B3: Nombre
            gspread.Cell(row=fila_base + 2, col=15, value=str(fila_datos.iloc[3])), # O3: Expediente/ID
            gspread.Cell(row=fila_base + 2, col=29, value=str(fila_datos.iloc[2])), # AC3: Edad
            gspread.Cell(row=fila_base + 3, col=3, value=str(fila_datos.iloc[6])),  # C4: Servicio/Cama
            gspread.Cell(row=fila_base + 4, col=27, value=str(fila_datos.iloc[1])), # AA5: Sexo
            gspread.Cell(row=fila_base + 5, col=2, value=str(fila_datos.iloc[8])),  # B6: Dx/Motivo
            gspread.Cell(row=fila_base + 8, col=col_dia, value="X")                 # C9-AG9: Marca día
        ]
        h_sheet.update_cells(lista_celdas, value_input_option='USER_ENTERED')
    except Exception as e:
        st.error(f"Error en mapeo: {e}")

# --- 3. INTERFAZ ---
st.title("🛡️ Vigilancia Activa de Piso")

# Botón para cargar pacientes disponibles
if st.button("🔍 Cargar lista de pacientes del Censo"):
    res = conectar_piso_activo()
    if res[0]:
        _, _, h_dat, _ = res
        df_full = pd.DataFrame(h_dat.get_all_records())
        st.session_state['df_piso_disponible'] = df_full
        st.success("Lista actualizada.")

if 'df_piso_disponible' in st.session_state:
    df = st.session_state['df_piso_disponible']
    
    # Creamos una columna para identificar al paciente en el selector
    df['display_name'] = df.apply(lambda x: f"{x.iloc[4]} | Cama: {x.iloc[6]}", axis=1)
    
    st.subheader("Selección de Pacientes")
    seleccionados = st.multiselect(
        "Selecciona los pacientes que quieres pasar a la Hoja de Vigilancia:",
        options=df['display_name'].tolist(),
        help="Solo los pacientes seleccionados serán procesados."
    )

    if st.button("🚀 Crear Plantillas para Seleccionados", type="primary"):
        if not seleccionados:
            st.warning("Por favor, selecciona al menos un paciente.")
        else:
            res = conectar_piso_activo()
            if res[0]:
                ss_sal, h_pla, h_dat, h_seg = res
                
                # Filtrar el dataframe original por los seleccionados
                df_procesar = df[df['display_name'].isin(seleccionados)]
                
                # Obtener donde termina la hoja de destino para no encimar
                # Buscamos en la columna B (Nombre) que es la fila base + 2
                col_nombres = h_seg.col_values(2)
                f_disp = len(col_nombres) + 1 if len(col_nombres) > 0 else 1
                
                # Si la hoja está vacía empezamos en 1, si no, saltamos al siguiente bloque
                if f_disp > 1:
                    # Ajuste para que empiece en una fila múltiplo de 10 o después del último bloque
                    f_disp = ((len(col_nombres) // 10) + 1) * 10 + 1

                prog = st.progress(0)
                status = st.empty()

                for idx, (i, row) in enumerate(df_procesar.iterrows()):
                    status.text(f"Creando bloque para: {row.iloc[4]}")
                    
                    # 1. Copiar Plantilla (Hoja 1 -> Hoja 2)
                    # Ajusta endRowIndex: 10 si tu bloque mide 10 filas
                    ss_sal.batch_update({"requests": [{"copyPaste": {
                        "source": {"sheetId": h_pla.id, "startRowIndex": 0, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
                        "destination": {"sheetId": h_seg.id, "startRowIndex": f_disp - 1, "endRowIndex": f_disp + 9, "startColumnIndex": 0, "endColumnIndex": 35},
                        "pasteType": "PASTE_NORMAL"
                    }}]})
                    
                    # 2. Llenar Datos
                    actualizar_bloque_piso(h_seg, f_disp, row)
                    
                    f_disp += 10 # Salto de bloque
                    prog.progress((idx + 1) / len(df_procesar))
                    time.sleep(2.5) # Pausa anti-bloqueo de Google
                
                st.success(f"✅ Se han creado {len(df_procesar)} nuevas hojas de vigilancia.")
